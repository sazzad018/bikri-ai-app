from django.urls import path
from .views.facebook_oauth import facebook_oauth_init, FacebookOAuthCallbackView
from .views.whatsapp_oauth import whatsapp_oauth_init, WhatsAppOAuthCallbackView
from .views.whatsapp_templates import load_template_variables
from .views.api import OrderAPIView, OrderAPIDetailView

app_name = "business_profile"   

urlpatterns = [
    path('facebook/oauth/', facebook_oauth_init, name='facebook_oauth_init'),
    path('facebook/callback/', FacebookOAuthCallbackView.as_view(), name='facebook_oauth_callback'),
    path('whatsapp/oauth/', whatsapp_oauth_init, name='whatsapp_oauth_init'),
    path('whatsapp/callback/', WhatsAppOAuthCallbackView.as_view(), name='whatsapp_oauth_callback'),
    path('whatsapp/template-variables/', load_template_variables, name='load_template_variables'),

    # API
    path('api/orders/', OrderAPIView.as_view(), name='order_api_list_create'),
    path('api/orders/<int:order_id>/', OrderAPIDetailView.as_view(), name='order_api_detail'),
]