import json
import hmac
import hashlib
import logging
import base64
from types import SimpleNamespace

from django.views import View
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from pywa import WhatsApp
from pywa.types import Button, MessageType
from pywa.errors import WhatsAppError

logger = logging.getLogger(__name__)

class WhatsAppMessage:
    platform = "whatsapp"
    supported_attachment_types = ("image", "audio")

    def __init__(self, sender_id: str, recipient_id: str, sender_name: str, payload: dict, is_echo: bool = False):
        # For incoming messages: sender_id is user's phone, recipient_id is Business Phone Number ID
        # For echo messages: sender_id is Business Phone Number ID, recipient_id is user's phone
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.payload = payload
        
        self.mid: str = payload.get("id")
        self.text: str = ''
        self.attachments: list[tuple[str, str]] = [] # attachments as tuples (type, media_id)
        self.replied_to: str = None # message ID this message is replying to
        self.is_echo: bool = is_echo
        self.app_id: str = None # needed when is_echo
        self.user: SimpleNamespace = SimpleNamespace(name=sender_name, gender=None, profile_pic_url=None)
        
        self._access_token: str = None
        self.client: WhatsApp = None
        
        

        # Parse Replied Message Context
        if "context" in payload and "id" in payload["context"]:
            self.replied_to = payload["context"]["id"]

        msg_type = payload.get("type")

        # Parse Text
        if msg_type == "text":
            self.text = payload.get("text", {}).get("body", "")

        # Parse Attachments (Media)
        elif msg_type in self.supported_attachment_types:
            media_payload = payload.get(msg_type, {})
            media_id = media_payload.get("id")
            if media_id:
                self.attachments.append((msg_type, media_id))

        # Parse Interactive (Buttons / List Replies)
        elif msg_type == "interactive":
            interactive = payload.get("interactive", {})
            inter_type = interactive.get("type")
            
            if inter_type == "button_reply":
                self.text = interactive.get("button_reply", {}).get("title", "")
                self.postback_payload = interactive.get("button_reply", {}).get("id", "")
            elif inter_type == "list_reply":
                self.text = interactive.get("list_reply", {}).get("title", "")
                self.postback_payload = interactive.get("list_reply", {}).get("id", "")

        # Parse standard button reply (from templates)
        elif msg_type == "button":
            self.text = payload.get("button", {}).get("text", "")
            self.postback_payload = payload.get("button", {}).get("payload", "")

    def __str__(self):
        return f"WhatsAppMessage(sender_id={self.sender_id}, recipient_id={self.recipient_id}, mid={self.mid})"
    
    def init_attachment(self):
        """convert attachments id into url"""
        atts = self.attachments
        self.attachments = []
        for att_type, media_id in atts:
            media = self.client.get_media_url(media_id)
            content = self.client.download_media(url=media.url, in_memory=True)
            data_url = f"data:{media.mime_type};base64,{base64.b64encode(content).decode()}"
            self.attachments.append((att_type, data_url))

    @property
    def access_token(self):
        if not self._access_token:
            raise ValueError("Access token must be set before accessing the client.")
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        self._access_token = value
        self.client = WhatsApp(self.recipient_id, self.access_token)
        self.init_attachment()

    @staticmethod
    def _wrap_msg_response(func):
        """
        Decorator for wrapping pywa responses to SimpleNamespace.
        pywa usually returns the message ID as a string on success,
        or raises a WhatsAppError on failure.
        """
        def wrapper(*args, **kwargs):
            try:
                response = func(*args, **kwargs)
                mid = getattr(response, "id", None)
                return SimpleNamespace(success=True, mid=mid, error=None)
            except WhatsAppError as e:
                logger.error(f"WhatsApp API Error: {e}")
                return SimpleNamespace(success=False, mid=None, error=str(e))
            except Exception as e:
                logger.exception("Unexpected error in WhatsApp client")
                return SimpleNamespace(success=False, mid=None, error=str(e))
        return wrapper

    @_wrap_msg_response
    def mark_seen(self):
        return self.client.mark_message_as_read(self.mid)

    @_wrap_msg_response
    def start_typing(self):
        return self.client.indicate_typing(self.mid)

    @_wrap_msg_response
    def stop_typing(self):
        # The WhatsApp Cloud API currently does not support typing indicators.
        return "not_supported"

    @_wrap_msg_response
    def reply_text(self, text: str, quick_replies: list[str] = None):
        if quick_replies:
            # Convert quick replies to WhatsApp Interactive Buttons
            # Note: WhatsApp allows a maximum of 3 buttons
            buttons = [
                Button(title=qr_text, callback_data=qr_text) 
                for qr_text in quick_replies[:3]
            ]
            return self.client.send_message(
                to=self.sender_id,
                text=text,
                buttons=buttons
            )
        return self.client.send_message(to=self.sender_id, text=text)
    
    @_wrap_msg_response
    def reply_attachment(self, attachment_type: str, url: str):
        """
        Sends an attachment. Pywa has separate methods for different media types.
        """
        if attachment_type == "image":
            return self.client.send_image(to=self.sender_id, image=url)
        elif attachment_type == "audio":
            return self.client.send_audio(to=self.sender_id, audio=url)
        elif attachment_type == "video":
            return self.client.send_video(to=self.sender_id, video=url)
        elif attachment_type in ("document", "file"):
            return self.client.send_document(to=self.sender_id, document=url)
        else:
            raise ValueError(f"Unsupported attachment type for WhatsApp: {attachment_type}")

    @_wrap_msg_response
    def reply_template(self, template_name: str, language: str = "en_US", components: list = None):
        """
        WhatsApp relies heavily on Templates for initiating conversations.
        """
        return self.client.send_template(
            to=self.sender_id,
            name=template_name,
            language=language,
            components=components
        )


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppAdapterView(View):
    """
    Base View for handling WhatsApp Webhooks in a multi-tenant environment.
    """
    verify_token = None
    app_secret = None

    def verify_hmac_signature(self, request):
        # WhatsApp uses the exact same signature logic as Messenger
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
            
            if body.get('object') == 'whatsapp_business_account':
                for entry in body.get('entry', []):
                    # Extract the Business Phone Number ID from the payload (useful for multi-tenant)
                    
                    for change in entry.get('changes', []):
                        value = change.get('value', {})
                        
                        recipient_phone_id = value.get('metadata', {}).get('phone_number_id')
                        sender_name = value.get('contacts', [{}])[0].get('profile', {}).get('name')
                        for message_payload in value.get('messages', []):
                            try:
                                self.process_message(recipient_phone_id, sender_name, message_payload)
                            except Exception as e:
                                logger.exception("Error processing WhatsApp message") 
                                
                        echo_payloads = value.get('message_echoes', []) + value.get('smb_message_echoes', [])
                        for echo_payload in echo_payloads:
                            try:
                                self.process_message(recipient_phone_id, sender_name, echo_payload, is_echo=True)
                            except Exception as e:
                                logger.exception("Error processing WhatsApp echo message")

                        if change.get('field') in ('history', 'smb_app_state_sync'):
                            logger.info(
                                "Received WhatsApp coexistence %s webhook for phone %s",
                                change.get('field'),
                                recipient_phone_id,
                            )
                                
                return HttpResponse('EVENT_RECEIVED'.encode(), status=200)
            
            logger.error("Unsupported object type: %s", body.get('object'))
            return HttpResponse('NotFound'.encode(), status=404)
        except Exception as e:
            logger.exception("Error processing WhatsApp webhook")
            return HttpResponse('Internal Server Error'.encode(), status=500)

    def process_message(self, recipient_phone_id, sender_name, message_payload, is_echo=False):
        """Process a single messaging event"""
        if is_echo:
            sender_id = recipient_phone_id
            recipient_id = message_payload.get('to')
        else:
            sender_id = message_payload.get('from')
            recipient_id = recipient_phone_id
        
        if sender_id and recipient_id:
            msg = WhatsAppMessage(sender_id, recipient_id, sender_name, message_payload, is_echo=is_echo)
            self.on_message(msg)
        else:
            logger.error("Missing sender or recipient ID in payload: %s", message_payload)
            
    def on_message(self, msg: WhatsAppMessage):
        """
        Override to handle messages.
        Usage Example:
            msg.initialize_client(token="YOUR_WA_TOKEN")
            msg.reply_text("Hello from WhatsApp!")
        """
        pass