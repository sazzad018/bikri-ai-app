from django.urls import path
from .views import MessengerWebhookView, WhatsappWebhookView

urlpatterns = [
    path('messenger/', MessengerWebhookView.as_view(), name='messenger_webhook'),
    path('whatsapp/', WhatsappWebhookView.as_view(), name='whatsapp_webhook'),
]