from django.urls import re_path
from .views import MessengerWebhookView, WhatsappWebhookView

urlpatterns = [
    re_path(r'^messenger/?$', MessengerWebhookView.as_view(), name='messenger_webhook'),
    re_path(r'^whatsapp/?$', WhatsappWebhookView.as_view(), name='whatsapp_webhook'),
]