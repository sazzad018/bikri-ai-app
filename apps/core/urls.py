from django.urls import path, include
from .views import info_view, landing

urlpatterns = [
    path('', landing, name='landing'),
    path('i/<str:endpoint>/', info_view, name='info'),
    path('business-profile/', include('apps.business_profile.urls')),
    path('webhook/', include('apps.webhooks.urls')),
    path('credit/', include('apps.credit.urls')),
]
