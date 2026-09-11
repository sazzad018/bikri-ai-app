from django.contrib import admin
from .models import CreditPackage, PaymentAttempt, CreditTransaction
from apps.core.admin.mixins import AdminReadonlyMixin
from apps.core.admin import ModelAdmin
from unfold.admin import display
from django.utils.safestring import mark_safe
@admin.register(CreditPackage)
class CreditPackageAdmin(ModelAdmin):
    list_display = ['title', 'credits', 'price_bdt', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['title']
    ordering_field = 'order'
    hide_ordering_field = True

@admin.register(PaymentAttempt)
class PaymentAttemptAdmin(AdminReadonlyMixin, ModelAdmin):
    list_display = ['id', 'user', 'package', 'payment_method', 'status', 'manual_transaction_id', 'created_at', 'verify_url']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__email', 'id', 'manual_transaction_id']

    @display
    def verify_url(self, obj):
        if obj.status == 'pending':
            return mark_safe(f'<a class="text-primary-600 underline" href="{obj.verify_url}">Verify</a>')

    
@admin.register(CreditTransaction)
class CreditTransactionAdmin(AdminReadonlyMixin, ModelAdmin):
    list_display = ['user', 'amount', 'reason', 'created_at']
    list_filter = ['reason', 'created_at']
    search_fields = ['user__email']
