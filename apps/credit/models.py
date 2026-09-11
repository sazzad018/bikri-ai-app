import uuid
from django.db import models
from apps.core.models import BaseModel
from django.conf import settings
from django.core.validators import MinValueValidator
    
from django.db.models import Avg, Min
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class CreditPackage(BaseModel):
    title = models.CharField(verbose_name="Package Name", max_length=100)
    credits = models.PositiveIntegerField(help_text="Number of credits in this package")
    price_bdt = models.PositiveBigIntegerField(help_text="Price in BDT", validators=[MinValueValidator(1)]) # minimum price 1
    is_featured = models.BooleanField(default=False, help_text="Whether this package is featured")
    is_active = models.BooleanField(default=True, help_text="Whether this package is available for purchase")
    order = models.PositiveIntegerField(default=0, help_text="Order for display")
    site_config = models.ForeignKey('core.SiteConfig', on_delete=models.CASCADE, related_name='credit_packages', default=1)

    def __str__(self):
        return f"{self.title} - {self.credits} credits ({self.price_bdt} BDT)"

    class Meta:
        ordering = ['order', 'price_bdt']
        

class CreditTransaction(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='credit_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=3)
    reason = models.CharField(max_length=100)
    balance_after = models.DecimalField(max_digits=12, decimal_places=3)

    def __str__(self):
        return f"{self.reason}: {self.amount}"
    
    def save(self, *args, **kwargs):
        self.balance_after = self.user.credit_balance
        super().save(*args, **kwargs)

    @staticmethod
    def using_overview_data_list(user) -> list[float]:
        """
        Returns a chronological list of balance_after values over time 
        split into equal time intervals.
        """
        transactions = CreditTransaction.objects.filter(user=user).order_by('created_at').values_list('created_at', 'balance_after')
        count = transactions.count()

        # Edge cases: 0 or 1 transactions
        if count == 0:
            return [0.0]
        if count == 1:
            return [float(transactions[0][1])]

        start_time = transactions[0][0]
        end_time = timezone.now()
        num_buckets = min(count, 100)
        time_diff = end_time - start_time
        
        # Failsafe: if the transactions occurred in the exact same millisecond
        if time_diff.total_seconds() == 0:
            return [float(tx[1]) for tx in transactions][:num_buckets]

        interval = time_diff / num_buckets
        buckets = [[] for _ in range(num_buckets)]

        # Group transactions into their respective time buckets
        for created_at, balance_after in transactions:
            bucket_idx = int((created_at - start_time) / interval)
            bucket_idx = min(bucket_idx, num_buckets - 1)
            bucket_idx = max(bucket_idx, 0)
            buckets[bucket_idx].append(balance_after)

        result = []
        last_known_balance = 0.0

        for bucket in buckets:
            if bucket:
                avg_balance = sum(bucket) / len(bucket)
                result.append(int(avg_balance))
                last_known_balance = bucket[-1]
            else:
                result.append(int(last_known_balance))
        return result
    
class PaymentAttempt(BaseModel):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('bkash', 'bKash (Automatic)'),
        ('manual', 'Manual Payment'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='payment_attempts')
    amount = models.PositiveIntegerField()
    package = models.ForeignKey(CreditPackage, on_delete=models.SET_NULL, null=True, related_name='payment_attempts')
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bkash')
    manual_transaction_id = models.CharField(max_length=255, blank=True, null=True, help_text="Transaction ID submitted by user for manual payments")
    verified_at = models.DateTimeField(blank=True, null=True, help_text="When the manual payment was verified by admin")

    def __str__(self):
        return f"PaymentAttempt({self.user}, {self.amount}, {self.status})"
    
    def success(self):
        if self.status == 'pending':
            self.status = 'success'
            self.verified_at = timezone.now()
            self.save()
            self.user.credit_transaction(self.package.credits, reason='purchase')

    def fail(self):
        if self.status == 'pending':
            self.status = 'failed'
            self.save()

    @property
    def verify_url(self):
        verify_path = reverse('credit:admin_verify_payment', kwargs={'attempt_id': self.id})
        return f"{settings.SITE_URL}{verify_path}"
