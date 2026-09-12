from functools import wraps
import logging, json, datetime, zoneinfo, time, textwrap, base64
from axcent import Agent, OpenAIBackend, MockBackend, Image, Audio

# axcent is a custom python library for building ai agents created by me, github: https://github.com/ssshiponu/axcent

from apps.business_profile.models import BusinessProfile, Order
from apps.core.models.private import SiteConfig
from apps.core.utils import run_in_thread, parse_ai_response, try_except, clean_markdown
from django.conf import settings
from django.utils import timezone, timesince
from django.template.loader import render_to_string
from django.core.mail import send_mail
from .adaptors import MessengerAdapterView, WhatsAppAdapterView

logger = logging.getLogger(__name__)

class Mixin():
    verify_token = settings.FACEBOOK_VERIFY_TOKEN
    app_id = settings.FACEBOOK_APP_ID
    app_secret = settings.FACEBOOK_APP_SECRET
    
    def on_message(self, msg):
        def handle_message(msg):
            logger.info(msg.payload)
            def get_business_profile(id):
                business_profile = BusinessProfile.objects.filter(platform_id=id).first()
                if not business_profile:
                    logger.warning(f"Business profile not found for id: {id}")
                return business_profile

            if msg.is_echo:
                logger.info("ECHO")
                business_profile = get_business_profile(msg.sender_id)
                if not business_profile:
                    return True
                customer = business_profile.customers.filter(platform_id=msg.recipient_id).first()
                if not customer:
                    return True
                conversation = business_profile.conversations.filter(customer=customer).first()
                if not conversation:
                    return True

                message, message_created = conversation.messages.get_or_create(
                    mid=msg.mid,
                    defaults={"role": "human_agent", "content": msg.text}
                )


                # check if it is not sent from our platform
                if msg.platform == "messenger":
                    if str(msg.app_id) == self.app_id:
                        return True
                elif msg.platform == "whatsapp":
                    if not message_created:
                        return True
                    
                conversation.json.append({"role": "assistant", "content": f"Admin: {msg.text}"})
                conversation.auto_paused = True
                conversation.save()
                return True

            # get business profile and agent_object
            business_profile = get_business_profile(msg.recipient_id)
            if not business_profile:
                return True

            # provide access token to msg obj to be able to send reply back
            msg.access_token=business_profile.platform_access_token

            # get or create conversation and customer
            customer = business_profile.customers.filter(platform_id=msg.sender_id).first()
            if not customer:
                usr = msg.user
                customer, _ = business_profile.customers.get_or_create(
                    platform_id=msg.sender_id,
                    defaults={ "name": usr.name, "gender": usr.gender}
                )
                if usr.profile_pic_url:
                    customer.set_profile_picture(usr.profile_pic_url)
            conversation, conversation_created = business_profile.conversations.get_or_create(
                customer=customer
            )

            # initialize agent
            site_config = SiteConfig.get_solo()
            system_prompt = business_profile.knowledge or business_profile.get_system_prompt() or site_config.default_system_prompt or settings.DEFAULT_SYSTEM_PROMPT
            api_key = business_profile.get_api_key()
            ai_model = business_profile.ai_model or site_config.default_ai_model or settings.DEFAULT_AI_MODEL
            if not api_key:
                logger.error(f"Cannot initialize AI Agent: No OpenRouter API key found for business profile {business_profile.id}")
                return True
            agent = Agent(
                backend=OpenAIBackend(
                    base_url=settings.OPENROUTER_BASE_URL,
                    api_key=api_key,
                    model=ai_model,
                ),
            )
            if conversation.json:
                agent.history.data = conversation.json
            #set system prompt where role is system
            for i, m in enumerate(agent.history.data):
                if m["role"] == "system":
                    agent.history.data[i]["content"] = system_prompt
                    break

            #tool decorator
            def paid_tool(func):
                @agent.tool
                @wraps(func)
                def wrapper(*args, **kwargs):
                    cost = business_profile.credit_per_reply
                    if not business_profile.user.use_credit(cost, reason=f"tool_call:{func.__name__}"):
                        msg = f"System Error: Insufficient credits to execute {func.__name__}."
                        logger.error(msg)
                        return msg
                    conversation.tool_credit_used += cost
                    conversation.save()
                    return func(*args, **kwargs)
                return wrapper

            ### tools ###
            @paid_tool
            def send_attachments(ids: list[int]):
                """Send attachments to customer. you must use it to send media files like images, audio, video"""
                attachments = business_profile.media_files.filter(id__in=ids)
                sent_messages = {}
                for attachment in attachments:
                    if attachment:
                        url=attachment.get_abs_url()
                        sent = msg.reply_attachment(attachment.file_type, url)
                        if sent.success:
                            sent_messages[attachment.id] = "Sent"
                        else:
                            sent_messages[attachment.id] = "Failed to send"
                    else:
                        sent_messages[attachment.id] = "Not found"
                return f"Attachments: {sent_messages}"
            
            @paid_tool
            def send_products(ids: list[int]):
                """"Display multiple products in a rich cursorial card format, use for multiple products"""
                products = business_profile.products.filter(id__in=ids)
                if not products: return "Product: Incorrect product ids"
                sent = msg.reply_products([
                    {
                        "id": product.id,
                        "title": product.title,
                        "subtitle": product.get_subtitle(),
                        "image_url": product.get_image_abs_url(),
                        "buttons": product.get_cta_buttons(),
                    }
                    for product in products
                ])
                if not sent.success: return "Product: Failed to send"
                return f"Product(s) Sent: {ids}"
            
            @paid_tool
            def send_email(to: str, subject: str, body: str):
                """Send email notification to business admin or customer"""
                email_html = render_to_string("webhook/email/ai_mail.html", {"subject": subject, "body": body})
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[to],
                    html_message=email_html,
                )
                return f"Email sent to: {to}"
            
            @paid_tool
            def place_order(fields: dict):
                """
                Save an order to the database, must use it if a customer places an order
                fields example: {"key": "value", ...}
                """
                # validate fields
                if not isinstance(fields, dict):
                    return "Order not placed: fields must be an object."
                
                keys = set(business_profile.order_fields_list)
                if not all(k in keys for k in fields.keys()):
                    # check invalid keys
                    invalid_keys = [k for k in fields.keys() if k not in keys]
                    raise f"Order not placed. Invalid keys: {invalid_keys}.Keys must be: {sorted(keys)}"
                
                order = Order.objects.create(
                    business_profile=business_profile,
                    customer=customer,
                    conversation=conversation,
                    fields=fields
                )
                return f"Order placed, id: {order.id}"
                        
            @agent.tool
            def get_datetime():
                # local asia/dhaka
                tz = zoneinfo.ZoneInfo("Asia/Dhaka")
                return datetime.datetime.now(tz).isoformat()

            prompt = msg.text
            prompt_json = {}
            if conversation_created:
                prompt_json["user_name"] = customer.name
                if customer.gender:
                    prompt_json["user_name"] += f" ({customer.gender})"
            if msg.replied_to:
                replied_to_msg = conversation.messages.filter(mid=msg.replied_to).first()
                if replied_to_msg:
                    prompt_json["replied_to"] = textwrap.shorten(replied_to_msg.content, width=80, placeholder="...")
            # if conversation is last updated_at more than 5m ago, add it to prompt suffix
            if conversation.updated_at < timezone.now() - timezone.timedelta(minutes=5):
                prompt_json['last_activity'] = f"{timesince.timesince(conversation.updated_at)} ago"
            
            if prompt_json:
                prompt += "\n" + f'<context>{prompt_json}</context>'
                
            try:
                conversation.add_message(
                    mid = msg.mid,
                    role = "user",
                    content = prompt
                )
                conversation.json.append({"role": "user", "content": prompt})
                conversation.save()
            except Exception as e:
                logger.exception(e)
                return True
            

            can_reply, reason = conversation.can_ai_reply()
            if not can_reply:
                logger.info(f"Cannot reply to this conversation ({conversation.id}): {reason}")
                return True

            can_reply, reason = business_profile.can_ai_reply()
            if not can_reply:
                logger.info(f"Cannot reply to this business profile ({business_profile.id}): {reason}")
                return True
                
            media = []
            if msg.attachments:
                for att_type, url in msg.attachments:
                    if att_type == "image":
                        media.append(Image(url=url))
                    elif att_type == "audio":
                        media.append(Audio(data=base64.b64decode(url.split("base64,")[1]), mime_type="audio/ogg"))

            # mark seen and typing in different threads, without blocking main thread
            run_in_thread(msg.mark_seen)
            run_in_thread(msg.start_typing)
                
            logger.info(prompt)
            #ask
            reply = None
            try:
                reply = agent.ask(prompt, media=media)
                logger.info(reply)
            except Exception as e:
                logger.exception(e)
            if reply:
                text, response_json = parse_ai_response(reply)
                logger.info(text)
                text = clean_markdown(text)
                quick_replies = response_json.get("quick_replies", [])
                quick_replies = [textwrap.shorten(q, width=20, placeholder="...") for q in quick_replies][:3]

                # reply
                sent_response = msg.reply_text(text, quick_replies=quick_replies)
                
                # save response
                if sent_response.success:
                    conversation.add_message(
                        mid = sent_response.mid,
                        role = "assistant",
                        content = text
                    )
                    conversation.json = agent.history.data
                    # filter last 2 user messages from json, if both are same then remove one
                    history_data = conversation.json
                    if isinstance(history_data, list) and len(history_data) >= 2:
                        user_messages = [msg for msg in history_data if msg.get("role") == "user"]
                        if len(user_messages) >= 2:
                            last_two = user_messages[-2:]
                            if last_two[0].get("content") == last_two[1].get("content"):
                                history_data.remove(last_two[0])
                                conversation.json = history_data
                    if business_profile.user.has_credit(business_profile.credit_per_reply):
                        business_profile.user.use_credit(business_profile.credit_per_reply, reason="ai_reply")
                        conversation.message_credit_used += business_profile.credit_per_reply
                    conversation.save()


            msg.stop_typing()
            return True
        
        handle_message(msg)
        return True

    def on_comment(self, comment):
        def handle_comment(comment, business_profile):
            if comment.from_id == comment.page_id:
                return
            
            site_config = SiteConfig.get_solo()
            if not business_profile.user.has_credit(site_config.credit_per_comment):
                return

            comment_log = business_profile.comment_logs.create(
                psid=comment.from_id or "unknown",
                comment_text=comment.text, 
            )
            comment.access_token = business_profile.platform_access_token
            presets = business_profile.comment_presets.all()
            for preset in presets:
                keywords = preset.keywords or []
                if any(kw and kw.lower() in comment.text.lower() for kw in keywords):
                    comment.reply(preset.comment_text, destination=preset.reply_destination)
                    if comment_log:
                        comment_log.reply_text = preset.comment_text
                        comment_log.save()
                        business_profile.user.use_credit(site_config.credit_per_comment, reason="comment reply")
                    return
                
            if not business_profile.delete_negative_comments:
                return

            agent = Agent(
                backend=OpenAIBackend(
                    base_url=settings.OPENROUTER_BASE_URL,
                    api_key=business_profile.get_api_key(),
                    model="openai/gpt-oss-20b",
                )
            )
            prompt = f"Analyze the following comment and determine its negativity. Return ONLY a single number between -1.0 and 1.0, where -1.0 is extremely negative, 1.0 is extremely positive, and 0.0 is neutral. Do not return any other text.\n\nComment: {comment.text}"
            try:
                reply = agent.ask(prompt)
                score = float(reply.strip())
                logger.info(f"Comment: {comment.text} | Score: {score}")
                comment_log.sentiment_score = score
                if score < 0:
                    comment.delete()
                    comment_log.reply_text = "[Deleted - Negative Sentiment]"
                comment_log.save()
                business_profile.user.use_credit(site_config.credit_per_comment, reason="comment delete")

            except Exception as e:
                logger.error("Failed to parse negativity score or delete comment", exc_info=True)

        if comment.text:
            business_profile = BusinessProfile.objects.filter(platform_id=comment.page_id).first()
            if business_profile and business_profile.comments_reply_enabled:
                handle_comment(comment, business_profile)
                

    
class MessengerWebhookView(Mixin, MessengerAdapterView):
    "Combine Mixin and MessengerAdapterView"
    pass
    
class WhatsappWebhookView(Mixin, WhatsAppAdapterView):
    "Combine Mixin and WhatsAppAdapterView"
    pass
