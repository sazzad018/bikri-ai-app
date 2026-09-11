from django.urls import path
from . import views

app_name = 'credit'

urlpatterns = [
    path('buy/', views.buy_credit, name='buy_credit'),
    path('checkout/<int:package_id>/', views.checkout, name='checkout'),
    path('payment-callback/', views.payment_callback, name='payment_callback'),

    # Manual payment (only used when PAYMENT_ADAPTER = 'manual')
    path('submit-transaction/<uuid:attempt_id>/', views.submit_transaction_id, name='submit_transaction_id'),
    path('verify-payment/<uuid:attempt_id>/', views.admin_verify_payment, name='admin_verify_payment'),
]
