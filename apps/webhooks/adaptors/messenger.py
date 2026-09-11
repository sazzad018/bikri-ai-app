import json, hmac, hashlib
import logging, requests
from types import SimpleNamespace
from django.views import View
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from pymes import MessengerClient, Text, Attachment, QuickReply, GenericTemplate, GenericTemplateElement, Button
from apps.webhooks.utils import url_to_data_url
from django.conf import settings

logger = logging.getLogger(__name__)

class MessengerMessage():
    platform = "messenger"
    supported_attachment_types = ("image", "audio")
    sticker_mapping = {
        "369239263222822": "👍",
        "369239343222814": "👍",
        "369239383222810": "👍"
    }

    def __init__(self, sender_id, recipient_id, payload):
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.payload = payload
        
        self.mid: str = payload["mid"]
        self.text: str = ''
        self.attachments: list[tuple[str, str]] = [] # attachments as tuples (type, url)
        self.replied_to: str = None # message ID this message is replying to
        self.is_echo: bool = False
        self.app_id: str = None # needed when is_echo
        self._user: SimpleNamespace = None
        

        self._access_token: str = None
        self.client: MessengerClient = None

        
        if "reply_to" in payload:
            self.replied_to = payload["reply_to"]["mid"]

        if "text" in payload:
            self.text = payload["text"]

        if "attachments" in payload:
            attachments = payload["attachments"]
            for att in attachments:
                if att["type"] in self.supported_attachment_types:
                    # sticker comes as image. convert it into emoji
                    if att["type"] == "image" and "sticker_id" in att["payload"]:
                        sticker_id = att["payload"]["sticker_id"]
                        self.text += self.sticker_mapping.get(str(sticker_id), "[unknown sticker]")
                        continue
                    self.attachments.append((att["type"], url_to_data_url(att["payload"]["url"])))
                    
        if "is_echo" in payload:
            self.is_echo = payload["is_echo"]
            self.app_id = payload["app_id"]
        
        # postback    
        if "title" in payload and "payload" in payload:
            title = payload["title"]
            postback_payload = payload["payload"]
            if title.lower() == postback_payload.lower():
                self.text = title
            else:
                self.text = title + " " + postback_payload
            
        
    def __str__(self):
        return f"MessengerMessage(sender_id={self.sender_id}, recipient_id={self.recipient_id}, payload={self.payload})"

    @property
    def access_token(self):
        if not self._access_token:
            raise ValueError("Access token must be set before accessing the client.")
        return self._access_token

    @access_token.setter
    def access_token(self, token: str):
        self._access_token = token
        self.client = MessengerClient(token)

    @property
    def user(self):
        if not self._user:
            if not self.client:
                raise ValueError("Access token must be set before accessing the client.")
            # Note: Ensure self.client exists before calling this
            try:
                usr = self.client.fetch_user_profile(self.sender_id)
                if usr:
                    self._user = SimpleNamespace(
                        name=usr.get("first_name") + " " + usr.get("last_name"), 
                        gender=usr.get("gender"), 
                        profile_pic_url=usr.get("picture", {}).get("data", {}).get("url")
                    )
            except Exception as e:
                logger.exception(f"Error fetching user profile: {str(e)}")
                self._user = SimpleNamespace(name="Guest User", gender=None, profile_pic_url='https://placehold.net/avatar.png')
        return self._user
    
    @staticmethod
    def _wrap_msg_response(func):
        """
        Decorator for wrapping api response of messenger to SimpleNamespace.
        properties: 
            success: bool
            mid: str | None = None
            error: str | None = None
        """
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            mid = response.get("message_id", None)
            error = response.get("error", None)
            success = not error
            return SimpleNamespace(success=success, mid=mid, error=error)
        return wrapper

    @_wrap_msg_response
    def mark_seen(self):
        return self.client.send(self.sender_id, action="mark_seen")

    @_wrap_msg_response
    def start_typing(self):
        return self.client.send(self.sender_id, action="typing_on")

    @_wrap_msg_response
    def stop_typing(self):
        return self.client.send(self.sender_id, action="typing_off")

    @_wrap_msg_response
    def reply_text(self, text: str, quick_replies: list[str] = None):
        if quick_replies:
            return self.client.send(self.sender_id, QuickReply(text, buttons=quick_replies))
        return self.client.send(self.sender_id, Text(text))
    
    @_wrap_msg_response
    def reply_attachment(self, attachment_type: str, url: str):
        return self.client.send(self.sender_id, Attachment(attachment_type, url))
    
    @_wrap_msg_response
    def reply_products(self, elements: list[dict]):
        return self.client.send(self.sender_id, GenericTemplate(
            [GenericTemplateElement(
                title=element["title"],
                subtitle=element["subtitle"],
                image_url=element["image_url"],
                buttons=[Button(title=button, payload=f"product:{element['title']}") for button in element["buttons"]]
            ) for element in elements]
        ))

class Comment():
    def __init__(self, page_id: str, payload: dict):
        self.page_id = page_id
        self.from_id = payload.get("from", {}).get("id") or payload.get("sender_id")
        self.payload = payload
        self.comment_id = payload.get("comment_id") or payload.get("id")
        self.text = payload.get("message")
        self.access_token = None  # set in the view

    def __str__(self):
        return f"Comment(page_id={self.page_id}, comment_id={self.comment_id}, text={self.text})"
    
    def _check_access_token(self):
        if not self.access_token:
            raise ValueError("Access token must be set before accessing the client.")
    
    def reply(self, text: str, destination: str):
        self._check_access_token()

        if not text:
            raise ValueError("Text cannot be empty.")
        if destination not in ["comment", "inbox"]:
            raise ValueError(f"Invalid destination: {destination}")
            
        try:
            logger.debug(f"Sending reply to {destination}: {text}")
            if destination == "comment":
                url = f"{settings.FACEBOOK_GRAPH_API_URL}/{self.comment_id}/comments"
                payload = {
                    "message": text
                }

            elif destination == "inbox":
                url = f"{settings.FACEBOOK_GRAPH_API_URL}/{self.page_id}/messages"
                payload = {
                    "recipient": {
                        "comment_id": self.comment_id
                    },
                    "message": {
                        "text": text
                    }
                }
                
            r = requests.post(
                url, 
                params={"access_token": self.access_token}, 
                json=payload
            )
            
            logger.debug(f"Meta API Response: {r.text}")
            
            r.raise_for_status()
            return r.json()
            
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"Meta Graph API error replying to {destination}: {r.text}")
            raise http_err
        except Exception as e:
            logger.error(f"Unexpected error while sending comment reply: {str(e)}")
            raise e
        
    def delete(self):
        self._check_access_token()
        url = f"{settings.FACEBOOK_GRAPH_API_URL}/{self.comment_id}"
        try:
            r = requests.delete(url, params={"access_token": self.access_token})
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to delete comment {self.comment_id}: {str(e)}")
            raise e
        
@method_decorator(csrf_exempt, name='dispatch')
class MessengerAdapterView(View):
    """
    Base View for handling Messenger Webhooks. this used in multi tenant environment
    """
    verify_token = None
    app_secret = None

    def verify_hmac_signature(self, request):
        # Prefer SHA256
        signature = request.META.get('HTTP_X_HUB_SIGNATURE_256')
        if not signature:
            return False
        
        sha_name, signature_hash = signature.split('=')
        mac = hmac.new(
            self.app_secret.encode('utf-8'),
            request.body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(mac, signature_hash)
        
    def get(self, request, *args, **kwargs):
        """Handle Webhook Verification"""
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        if mode == 'subscribe' and token == self.verify_token and challenge:
            return HttpResponse(challenge)
        return HttpResponse('Forbidden'.encode(), status=403)

    def post(self, request, *args, **kwargs):
        """Handle Incoming Events"""
        try:
            if not self.verify_hmac_signature(request):
                logger.error("HMAC signature verification failed")
                return HttpResponse('Forbidden'.encode(), status=403)
            
            body = json.loads(request.body)
            if body.get('object') == 'page':
                for entry in body.get('entry', []):
                    for event in entry.get('messaging', []):
                        try:
                            self.process_event(event)
                        except Exception as e:
                            logger.exception(f"Error processing event")
                            
                    for change in entry.get('changes', []):
                        try:
                            self.process_change(entry.get('id'), change)
                        except Exception as e:
                            logger.exception(f"Error processing change")
                        # return success if also fail instead of retrying
                return HttpResponse('EVENT_RECEIVED'.encode(), status=200)
            logger.error("Unsupported object type: %s", body.get('object'))
            return HttpResponse('NotFound'.encode(), status=404)
        except Exception as e:
            logger.exception(f"Error processing webhook")
            return HttpResponse('Internal Server Error'.encode(), status=500)

    def process_event(self, event):
        """Process a single messaging event"""
        sender_id = event['sender']['id']
        recipient_id = event['recipient']['id']
        payload = None
        supported_events = ['message', 'postback']

        for e in supported_events:
            if e in event:
                payload = event[e]
                msg = MessengerMessage(sender_id, recipient_id, payload)
                self.on_message(msg)
                break
        else:
            logger.error("Unsupported event: %s", event)

    def process_change(self, page_id, change):
        if change.get('field') == 'feed':
            value = change.get('value', {})
            if value.get('item') == 'comment' and value.get('verb') == 'add':
                comment = Comment(page_id, value)
                self.on_comment(comment)
            
        
    def on_message(self, msg: MessengerMessage):
        """Override to handle messages"""
        pass


    def on_comment(self, comment: Comment):
        """Override to handle comments"""
        pass
