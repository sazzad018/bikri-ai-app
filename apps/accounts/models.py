from decimal import Decimal

from django.db import models
from apps.core.models import BaseModel
from django.contrib.auth.models import AbstractUser
from .manager import CustomUserManager
from django.db.models import F
from django.core.validators import MinValueValidator

class User(AbstractUser):
    objects = CustomUserManager()
    phone_number = models.CharField(max_length=15, null=True)
    picture = models.ImageField(upload_to='users', null=True, blank=True)
    ip_address = models.CharField(max_length=15, null=True, blank=True)
    note = models.TextField(null=True, blank=True, help_text="Internal notes about the user")
    credit_balance = models.DecimalField(max_digits=12, decimal_places=3, default=0, validators=[MinValueValidator(0)], help_text="User's current credit balance")
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=True)
    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return "-"

    def log(self, action: str):
        return self.activity_logs.create(log=action)

    def notify(self, type: str, title: str, message: str):  
        return self.notifications.create(type=type, title=title, message=message)
        
    def has_new_notifications(self):
        return self.notifications.filter(is_read=False).exists()
    
    def has_credit(self, amount) -> bool:
        return self.credit_balance >= Decimal(amount)

    def credit_transaction(self, amount, reason: str):
        amount = Decimal(amount)
        User.objects.filter(pk=self.pk).update(credit_balance=F('credit_balance') + amount)
        self.refresh_from_db(fields=['credit_balance'])
        self.credit_transactions.create(amount=amount, reason=reason)
        return True

    def use_credit(self, amount, reason: str) -> bool:
        amount = Decimal(amount)
        if self.has_credit(amount):
            self.credit_transaction(-amount, reason=reason)
            return True
        return False
    
    def get_popup(self):
        """ Get the most recent popup that hasn't been read by the user """
        popup = self.popups.exclude(users_read=self).order_by('-created_at').first()
        if popup:
            popup.users_read.add(self)
            popup.save()
        return popup
    
    class Meta:
        ordering = ['-date_joined', 'email']
    

class Notification(BaseModel):
    TYPE_CHOICES = [
        ('helpful', 'Helpful'),
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]

    TYPE_ICON_MAP = {
        'helpful': 'brain',
        'info': 'info',
        'success': 'check-circle',
        'warning': 'triangle-alert',
        'error': 'circle-x',
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    
    def get_icon(self):
        return self.TYPE_ICON_MAP.get(self.type, 'info')

    def get_variant(self):
        mapping = {
            'helpful': 'primary',
            'info': 'primary',
            'success': 'success',
            'warning': 'warning',
            'error': 'danger',
        }
        return mapping.get(self.type, 'info')

class ActivityLog(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    log = models.CharField(max_length=255)
    
    def __str__(self):
        return f"[{self.created_at}] {self.log}"