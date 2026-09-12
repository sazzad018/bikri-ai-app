import requests
import csv
import io
import textwrap
from django.db import models
from decimal import Decimal
from apps.core.models import BaseModel, SiteConfig
from apps.core.utils import parse_ai_response, guess_file_type, count_tokens
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings
from django.core.files.base import ContentFile
from django_softdelete.models import SoftDeleteModel
from django_jsonform.models.fields import JSONField
from .system_prompt import render_system_prompt
import logging

logger = logging.getLogger(__name__)

def default_order_fields():
    return [
        { 'key': 'name', 'ask_user': True },
        { 'key': 'phone', 'ask_user': True },
        { 'key': 'address', 'description': 'Full Shipping Address', 'ask_user': True },
        { 'key': 'product', 'description': 'Product Name', 'ask_user': False },
        { 'key': 'quantity', 'description': 'Quantity', 'ask_user': True },
        { 'key': 'total', 'description': 'Total', 'ask_user': False },
    ]

def default_order_fields_data():
    return {
        k["key"]: '' for k in default_order_fields()
    }

def default_preset_keywords():
    return ['']

class BusinessProfile(BaseModel):
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('whatsapp', 'Whatsapp'),
    ]

    ORDER_FIELD_SCHEMA = {
        'type': 'list',
        'items': {
            'type': 'dict',
            'keys': {
                'key': {
                    'type': 'string', 
                    'required': True,
                    'help_text': 'English only'
                },
                'description': {
                    'type': 'string', 
                    'required': False,
                    'help_text': 'Optional'
                },
                'ask_user': {
                    'type': 'boolean', 
                    'required': True, 
                    'default': True,
                    'title': 'Should be asked from user in chat?' # Replaces help_text
                },
            }
        }
    }

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='business_profiles')
    name = models.CharField(max_length=100)
    profile_pic = models.ImageField(upload_to='profile_pic', blank=True, null=True)

    platform_id = models.CharField(max_length=100, verbose_name="ID on platform")
    platform_name = models.CharField(max_length=100, choices=PLATFORM_CHOICES)
    waba_id = models.CharField(max_length=100, blank=True, null=True, help_text="WhatsApp Business Account ID")
    _platform_access_token = models.CharField(db_column='platform_access_token', max_length=1024, blank=True, null=True)
    
    system_prompt = models.TextField(blank=True, null=True, help_text="Instructions for the AI to follow.")
    business_info = models.TextField(blank=True, null=True, help_text="Provide information about your business.")
    order_fields = JSONField(schema=ORDER_FIELD_SCHEMA, default=default_order_fields)

    ai_model = models.CharField(max_length=100, blank=True, null=True)
    knowledge = models.TextField(blank=True, null=True) #readonly in frontend   
    knowledge_token = models.PositiveIntegerField(default=0) #readonly in frontend, auto calculated from site config based system prompt token count
    openrouter_api_key = models.CharField(max_length=1024, blank=True, null=True, help_text="This will be used if provided otherwise default.")
    reply_enabled = models.BooleanField(verbose_name="AI Reply", default=True, help_text="Enable or disable ai")
    auto_pause = models.BooleanField(verbose_name="Auto Pause on Admin reply", default=True)
    pause_timeout = models.PositiveIntegerField(verbose_name="Auto Pause Timeout (minutes)", default=15, help_text="Time to auto resume replying after paused.")
    comments_reply_enabled = models.BooleanField(verbose_name="Preseted Comment Reply", default=True, help_text="Enable or disable preseted comment reply")
    delete_negative_comments = models.BooleanField(verbose_name="Delete Negative Comment", default=False, help_text="Enable or disable deleting negative comments")

    #api & webhook
    api_enabled = models.BooleanField(default=False)
    api_key = models.CharField(max_length=1024, blank=True, unique=True, null=True)
    webhook_enabled = models.BooleanField(default=False)
    webhook_url = models.URLField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def platform_access_token(self):
        token = settings.FERNET.decrypt(self._platform_access_token.encode()).decode()
        return token

    @platform_access_token.setter
    def platform_access_token(self, value):
        """Encrypts the value when assigned."""
        self._platform_access_token = settings.FERNET.encrypt(value.encode()).decode()

    @property
    def credit_per_reply(self) -> Decimal:
        site_config = SiteConfig.get_solo()
        return (
            site_config.credit_per_reply
            + Decimal(self.knowledge_token) * site_config.credit_per_reply_increment
        ).quantize(Decimal('0.001'))

    @property
    def order_fields_list(self):
        return [k.get("key") for k in self.order_fields]

    def generate_products_csv_text(self) -> str:
        # Prefetch related media files for all products to reduce queries
        products = self.products.filter(is_active=True).prefetch_related('related_media_files')
        if not products: 
            return ""

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['id', 'title', 'description', 'price', 'related_media_file_ids'])

        for product in products:
            related_media_file_ids = ",".join([str(media_file.id) for media_file in product.related_media_files.all()])
            writer.writerow([product.id, product.title, product.description, product.price, related_media_file_ids])

        return output.getvalue()
    
    def generate_media_files_csv_text(self) -> str:
        media_files = self.media_files.all()
        if not media_files: 
            return ""

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['id', 'type', 'transcription'])

        for media_file in media_files:
            writer.writerow([ media_file.id, media_file.file_type, media_file.transcription ])

        return output.getvalue()
            
    def get_system_prompt(self):
        return render_system_prompt(
            system_prompt = self.system_prompt,
            business_info = self.business_info,
            products = self.generate_products_csv_text(),
            media_files = self.generate_media_files_csv_text(),
            order_fields = self.order_fields,
        )

    def update_knowledge(self):
        try:
            knowledge = self.get_system_prompt()
            knowledge_token = count_tokens(knowledge)
            BusinessProfile.objects.filter(id=self.id).update(knowledge=knowledge, knowledge_token=knowledge_token)
        except Exception as e:
            logger.exception(f"Failed to update knowledge: {e}")

    def can_ai_reply(self):
        if not self.reply_enabled:
            return False, "reply disabled"
        else:
            # check if user has credit (allow superuser to test)
            if self.user.is_superuser or self.user.has_credit(self.credit_per_reply):
                return True, ""
            else:
                return False, "insufficient credits"
            
    def get_api_key(self):
        return self.openrouter_api_key or SiteConfig.get_solo().global_openrouter_api_key or settings.OPENROUTER_API_KEY
        
    def sync_whatsapp_templates(self):
        if self.platform_name != 'whatsapp' or not self.waba_id:
            raise Exception("Not a WhatsApp account or WABA ID missing.")
        
        url = f"{settings.FACEBOOK_GRAPH_API_URL}/{self.waba_id}/message_templates"
        params = {"access_token": self.platform_access_token}
        response = requests.get(url, params=params)
        
        if not response.ok:
            raise Exception(f"Failed to fetch templates. Please try again!")
            
        data = response.json().get('data', [])
        synced_count = 0
        for item in data:
            WhatsappTemplate.objects.update_or_create(
                business_profile=self,
                template_id=item.get('id'),
                defaults={
                    'name': item.get('name'),
                    'language': item.get('language'),
                    'status': item.get('status'),
                    'category': item.get('category'),
                    'components': item.get('components', []),
                }
            )
            synced_count += 1
        return synced_count

    def save(self, *args, **kwargs):
        if self.api_enabled and not self.api_key:
            import secrets
            self.api_key = f"bkai_{secrets.token_hex(24)}"

        # slugify order fields keys
        for order_field in self.order_fields:
            order_field["key"] = slugify(order_field["key"])
        
        super().save(*args, **kwargs)

    class Meta:
        unique_together = [('platform_id', 'platform_name')]
        ordering = ['-updated_at', '-created_at']
        

class Product(BaseModel):
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="products")
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=512, blank=True, null=True, help_text="Description of the product, including variants, discounts and more.")
    price = models.IntegerField(help_text="In BDT")
    is_active = models.BooleanField(default=True, help_text="Enable or disable product")
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-updated_at', '-created_at']
    
    def get_subtitle(self):
        currency_symbol = '৳'
        desc = (self.description or '').strip()
        subtitle = f"{currency_symbol}{self.price}"
        if desc:
            subtitle += f" • {desc}"
        subtitle = textwrap.shorten(subtitle, width=80, placeholder="...")
        return subtitle

    def get_cta_buttons(self):
        return ["Buy Now", "Details"]
    
    def get_image(self):
        image_obj = self.related_media_files.filter(file_type='image').first()
        if image_obj:
            return image_obj.file
        return None

    def get_image_abs_url(self):
        image = self.related_media_files.filter(file_type='image').first()
        if not image:
            return 'https://placehold.co/150/?text=No+Image'
        return image.get_abs_url()
    
    def get_image_url(self):
        image = self.related_media_files.filter(product=self, file_type='image').first()
        if not image:
            return 'https://placehold.co/150/?text=No+Image'
        return image.file.url
        

class MediaFiles(BaseModel):
    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'File'),
    ]
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="media_files")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="related_media_files", null=True, blank=True)
    file = models.FileField(upload_to='media_files')
    file_type = models.CharField(max_length=100, choices=FILE_TYPE_CHOICES, default='file')
    transcription = models.TextField(null=True, blank=True, max_length=512, help_text="AI Cannot see the file every time. Describe the content of the file for ai to understand.")
    priority = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.file.name
    
    class Meta:
        ordering = ['priority', '-updated_at', '-created_at']
        verbose_name = 'Media File'
        verbose_name_plural = 'Media Files'
    
    def get_abs_url(self):
        return f'{settings.SITE_URL}{self.file.url}'
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_type = guess_file_type(self.file.name)
        super().save(*args, **kwargs)
        

class Customer(BaseModel):
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="customers")
    platform_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    profile_pic = models.ImageField(upload_to='profile_pic', blank=True, null=True)
    gender = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    
    def set_profile_picture(self, url):
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            self.profile_pic.save(
                f"{self.name.lower().replace(' ', '_')}.jpg",
                ContentFile(r.content),
                save=False
            )
            self.save()

class Conversation(SoftDeleteModel, BaseModel):
    CONV_SCHEMA = {
        "type": "array",
        "title": "Conversation History",
        "items": {
            "type": "object",
            "title": "Message",
            "required": ["role", "content"],
            "properties": {
            "role": {
                "type": "string",
                "title": "Role",
                "enum": ["system", "user", "assistant", "tool"],
            },
            "content": {
                "type": "string",
                "title": "Content",
                "widget": "textarea",
                #max height
                "ui:options": {
                "rows": 5
                }
            },
            "tool_call_id": {
                "type": "string",
                "title": "TCID (Optional)",
            }
            }
        }
    }
    customer = models.ForeignKey(Customer, null=True, on_delete=models.CASCADE, related_name='conversations')
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="conversations")
    reply_enabled = models.BooleanField(default=True)
    auto_paused = models.BooleanField(default=False, help_text="If paused due to admin reply")
    json = JSONField(schema=CONV_SCHEMA, default=list)
    message_credit_used = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    tool_credit_used = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    def __str__(self):
        return self.customer.name
    
    
    def add_message(self, **kwargs):
        self.messages.create(**kwargs)
    
    def get_json(self):
        new_conv = []
        for m in self.json or []:
            content = m.get("content") or ""
            if m["role"] == "system":
                continue
            # remove <context>...</context> from message
            if "<context>" in content:
                content = content.split("<context>")[0]
            if m["role"] == "assistant":
                text, json = parse_ai_response(content)
                m |= json
                content = text
            if m["role"] == "tool":
                continue
            if content:
                m["content"] = content
                new_conv.append(m)
                
        return new_conv
    
    def pause(self):
        """Pause replying to this conversation"""
        self.auto_paused = True
        self.save()

    def resume(self):
        """Resume replying to this conversation"""
        self.auto_paused = False
        self.save()
        
    def can_ai_reply(self):
        """if updated_at is more than 15min when paused. it can reply"""
        if self.business_profile.auto_pause:
            if self.updated_at < timezone.now() - timezone.timedelta(minutes=self.business_profile.pause_timeout):
                self.resume()
        if self.auto_paused or not self.reply_enabled:
            return False, "reply disabled"
        return True, ""


class Message(SoftDeleteModel, BaseModel):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('human_agent', 'Human Agent'),
    ]
    mid = models.CharField(max_length=255, unique=True, help_text="Message ID from platform")
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=100, choices=ROLE_CHOICES)
    content = models.TextField()
    
    def __str__(self):
        return self.content
    
class Attachment(BaseModel):
    """temporarily save attachments urls"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="attachments")
    url = models.URLField()
    file_type = models.CharField(max_length=255)
    
    def __str__(self):
        return self.url
    
class Order(SoftDeleteModel, BaseModel):
    FIELDS_SCHEMA = {
        "type": "dict",
        "keys": {},
        "additionalProperties": True
    }
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('paused', 'Paused'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='orders')
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, related_name='orders')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='orders')
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])
    fields = JSONField(schema=FIELDS_SCHEMA, default=default_order_fields_data)
    
    def __str__(self):
        return f"Order: {self.id}"
    
class CommentPreset(BaseModel):
    KEYWORD_SCHEMA = {
        'type': 'array',
        'items': {
            'type': 'string'
        }
    }
    REPLY_DESTINATION_CHOICES = [
        ('comment', 'Comment'),
        ('inbox', 'Inbox'),
    ]
    business_profile = models.ForeignKey(BusinessProfile, verbose_name="Facebook Page", on_delete=models.CASCADE, related_name="comment_presets")
    keywords = JSONField(schema=KEYWORD_SCHEMA, default=default_preset_keywords, help_text="List of keywords to match for this preset")
    reply_destination = models.CharField(max_length=100, choices=REPLY_DESTINATION_CHOICES, default=REPLY_DESTINATION_CHOICES[0][0])
    comment_text = models.TextField(verbose_name="Reply", help_text="The automated reply text if a keyword matches")

    def __str__(self):
        return f"Comment Preset for {self.business_profile.name}"
    
class CommentLog(BaseModel):
    business_profile = models.ForeignKey(BusinessProfile, verbose_name="Facebook Page", on_delete=models.CASCADE, related_name="comment_logs")
    psid = models.CharField(max_length=100)
    comment_text = models.TextField()
    reply_text = models.TextField(blank=True, null=True)
    sentiment_score = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.comment_text}"

class WhatsappTemplate(BaseModel):
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="whatsapp_templates")
    template_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    language = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    components = models.JSONField(default=list)

    def __str__(self):
        return f"{self.name} ({self.language})"
        
    class Meta:
        ordering = ['-updated_at']
    