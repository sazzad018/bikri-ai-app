from django.urls import path, include
from .views import info_view, landing

urlpatterns = [
    path('', landing, name='landing'),
    path('i/<str:endpoint>/', info_view, name='info'),
    path('privacy-policy/', info_view, {'endpoint': 'privacy-policy'}, name='privacy_policy_direct'),
    path('privacy/', info_view, {'endpoint': 'privacy-policy'}, name='privacy_direct'),
    path('terms-of-service/', info_view, {'endpoint': 'terms-of-service'}, name='terms_of_service_direct'),
    path('terms/', info_view, {'endpoint': 'terms-of-service'}, name='terms_direct'),
    path('data-deletion/', info_view, {'endpoint': 'privacy-policy'}, name='data_deletion_direct'),
    path('business-profile/', include('apps.business_profile.urls')),
    path('webhook/', include('apps.webhooks.urls')),
    path('credit/', include('apps.credit.urls')),
]
