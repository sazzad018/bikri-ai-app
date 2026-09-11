from decimal import Decimal

from django.db import models
from django.conf import settings
from django_ckeditor_5.fields import CKEditor5Field
from django_jsonform.models.fields import JSONField

from .homepage import HomePage
from apps.core.models import BaseModel

class SiteConfig(models.Model):
    credit_per_reply = models.DecimalField(max_digits=8, decimal_places=3, default=Decimal('1'), help_text="Starting credit per ai reply.")
    credit_per_reply_increment = models.DecimalField(max_digits=8, decimal_places=6, default=Decimal('0.0002'), help_text="Credit increment rate per token.")
    credit_per_comment = models.DecimalField(max_digits=8, decimal_places=3, default=Decimal('0.1'), help_text="Sentiment analysis credit per comment.")
    free_credits_on_signup = models.PositiveIntegerField(default=10)
    default_system_prompt = models.TextField(default=settings.DEFAULT_SYSTEM_PROMPT, help_text="Default system prompt for the AI.")
    default_business_info = models.TextField(default=settings.DEFAULT_BUSINESS_INFO, help_text="Default business information for the AI.")
    default_ai_model = models.CharField(max_length=100, default=settings.DEFAULT_AI_MODEL, help_text="Default AI model name from OpenRouter, e.g. provider/model")
    global_openrouter_api_key = models.CharField(max_length=1024, blank=True, null=True, help_text="Global OpenRouter API key.")
    # TODO: add more configuration options as needed
    def __str__(self):
        return "Cholbe AI Site Configuration"

    @classmethod
    def get_solo(cls):
        return SiteConfig.objects.get_or_create(pk=1)[0]

class InfoPage(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(null=True, blank=True)
    content = CKEditor5Field(config_name='extends')

    def __str__(self):
        return self.title

    def get_url(self):
        return f"/i/{self.slug}"
    
class Popup(BaseModel):
    name = models.CharField(max_length=100)
    content = CKEditor5Field(config_name='extends')
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='popups', help_text="Users who will see this popup.")
    BUTTONS_SCHEMA = {
        "type": "array",
        "items": {
            "type": "object",
            "keys": {  # 'keys' is preferred over 'properties' in django-jsonform
                "label": {"type": "string", "minLength": 1},
                "action": {
                    "type": "string",
                    "choices": ["url", "url_new_tab", "close"], # 'choices' is preferred over 'enum'
                    "description": "Button behavior when clicked."
                },
                "variant": {
                    "type": "string",
                    "choices": ["primary", "secondary", "info", "success", "warning", "danger"],
                    "default": "primary",
                    "description": "Visual style variant."
                },
                "url": {
                    "type": "string",
                    "format": "uri",
                    "description": "Target URL for navigation actions."
                }
            },
            # Remove 'url' from static required fields; we will handle it dynamically in Python
            "required": ["label", "action"], 
            "additionalProperties": False
        },
        "minItems": 1,
        "description": "A list of buttons for the popup configuration."
    }
    buttons = JSONField(default=list, schema=BUTTONS_SCHEMA)
    users_read = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='popup_read', blank=True, help_text="Users who have read (closed) this popup.")

    def __str__(self):
        return self.name
    
    def clean(self):
        super().clean()
        for button in self.buttons:
            action = button.get('action')
            if action in ['url', 'url_new_tab'] and not button.get('url'):
                from django.core.exceptions import ValidationError
                raise ValidationError(f"Button '{button.get('label')}' requires a URL for action '{action}'.")