from django.contrib import admin
from django.db.models import Exists, OuterRef, Q, Count, Sum
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from django.urls import reverse
from unfold.admin import display, TabularInline
from unfold.sections import TableSection
from unfold.contrib.filters.admin import RangeNumericFilter, RangeDateFilter, DropdownFilter

from apps.core.utils import profile_html
from apps.credit.models import PaymentAttempt, CreditPackage
from .models import User
from django.utils import timezone
from datetime import timedelta
from apps.credit.models import CreditTransaction
from apps.core.admin import ModelAdmin
from allauth.account.models import EmailAddress
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import messages
from django.shortcuts import render, redirect
from unfold.decorators import action


admin.site.empty_value_display = 'N/A'

class PaymentInline(TabularInline):
    hide_title = True
    model = PaymentAttempt
    extra = 0
    fields = ['package', 'amount', 'status', 'created_at', 'verified_at']
    readonly_fields = fields

    def get_queryset(self, request):
        #show only successful payments
        qs = super().get_queryset(request)
        return qs.filter(status="success").order_by('-created_at')

    def has_add_permission(self, *args, **kwargs):
        return False
    def has_change_permission(self, *args, **kwargs):
        return False
    def has_delete_permission(self, *args, **kwargs):
        return False
    
#user filter
class UserTypeFilter(DropdownFilter):
    title = 'User Type'
    parameter_name = 'user_type'

    def lookups(self, request, model_admin):
        return [
            ('free', 'Free Users'),
            ('paid', 'Paid Users'),
            ('small_package', 'Small Package Buyers'),
            ('multiple_package', 'Multiple Package Buyers'),
            ('recent', 'Recent Users (1d)'),
            ('inactive', 'Inactive Users (30d+)'),
        ]
    
    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset

        # Setup a base subquery for successful payments to check existence efficiently
        successful_payments = PaymentAttempt.objects.filter(
            user=OuterRef("pk"), 
            status="success"
        )

        if value == 'free':
            # No successful PaymentAttempts at all
            return queryset.annotate(
                has_paid=Exists(successful_payments)
            ).filter(has_paid=False)

        elif value == 'paid':
            # Exactly 1 successful PaymentAttempt
            return queryset.annotate(
                success_count=Count('payment_attempts', filter=Q(payment_attempts__status='success'))
            ).filter(success_count=1)

        elif value == 'small_package':
            small_package = CreditPackage.objects.filter(is_active=True).order_by('price_bdt').first()
            if not small_package:
                return queryset.none()
            
            return queryset.filter(
                payment_attempts__status='success',
                payment_attempts__package=small_package
            ).distinct()

        elif value == 'multiple_package':
            return queryset.annotate(
                success_count=Count('payment_attempts', filter=Q(payment_attempts__status='success'))
            ).filter(success_count__gte=2)

        elif value == 'recent':
            one_day_ago = timezone.now() - timedelta(days=1)
            return queryset.filter(last_login__gte=one_day_ago)

        elif value == 'inactive':
            thirty_days_ago = timezone.now() - timedelta(days=30)
            return queryset.filter(Q(last_login__lt=thirty_days_ago) | Q(last_login__isnull=True))

        return queryset
    

class BusinessProfileSection(TableSection):
    title = 'Business Profiles'
    related_name='business_profiles'
    fields=list_display = ['profile', 'platform', 'credit_per_reply', 'reply_enabled']

    def profile(self, obj):
        image_url = ''
        if obj.profile_pic:
            image_url = obj.profile_pic.url
        elif obj.platform_name == "facebook":
            image_url = "/static/img/gray_facebook.jpg"
        elif obj.platform_name == "whatsapp":
            image_url = "/static/img/gray_whatsapp.jpg"
        return profile_html(image_url, obj.name, href=reverse('admin:business_profile_businessprofile_change', args=[obj.pk]))
        
    def platform(self, obj):
        return obj.platform_name
    

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    ordering = ['-date_joined', 'email']
    search_fields = ['first_name', 'last_name', 'email']
    list_filter = [ UserTypeFilter, 'is_active', 'is_superuser', ('credit_balance', RangeNumericFilter), ('date_joined', RangeDateFilter), ('last_login', RangeDateFilter)]
    list_filter_submit = True
    list_display = ['name', 'email', 'credit_balance', 'is_active', 'is_superuser', 'last_login', 'date_joined']
    readonly_fields = ['last_login', 'date_joined', 'email', 'credit_balance', "total_successful_payment_attempts", "total_amount_paid", "first_payment_date", "last_payment_date"]
    actions = ['send_email_action']
    list_sections = [BusinessProfileSection]
    inlines = [PaymentInline]

    fieldsets = (
        ('Personal info', {
            'fields': (('email','phone_number'), ('first_name', 'last_name')),
        }),
        ("", {
            'fields': ('credit_balance', 'note'),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_superuser', 'groups', 'user_permissions'),
            "classes": ('collapse',),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    @display()
    def name(self, obj):
        if not obj.first_name or not obj.last_name:
            return None
        return f"{obj.first_name} {obj.last_name}"
    
    def has_add_permission(self, request):
        return False
    
    @display(description="Total Successful Payments")
    def total_successful_payment_attempts(self, obj):
        return obj.payment_attempts.filter(status='success').count()

    @display(description="Total Amount Paid")
    def total_amount_paid(self, obj):
        return obj.payment_attempts.filter(status='success').aggregate(Sum('amount'))['amount__sum'] or 0
    
    @display(description="First Payment Date")
    def first_payment_date(self, obj):
        return obj.payment_attempts.filter(status='success').order_by('created_at').first().created_at.strftime("%b %d, %Y, %I:%M %p")
    
    @display(description="Last Payment Date")
    def last_payment_date(self, obj):
        return obj.payment_attempts.filter(status='success').order_by('-created_at').first().created_at.strftime("%b %d, %Y, %I:%M %p")
    

    def get_fieldsets(self, request, obj = None):
        fs = list(super().get_fieldsets(request, obj))
        if not any(f[0] == "Payment Stats" for f in fs):
            fs.append((
                    "Payment Stats",
                    {
                        "fields": (("total_successful_payment_attempts", "total_amount_paid"), ("first_payment_date", "last_payment_date")),
                    }
                ))
        return fs

    @action(description="Send Email")
    def send_email_action(self, request, queryset):
        #allow maximum 50 users to send email
        if queryset.count() > 50:
            messages.error(request, "You can only send email to maximum 50 users at a time.")
            return redirect(request.get_full_path())

        if 'apply' in request.POST:
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            if not subject or not message:
                messages.error(request, "Subject and message are required.")
                return redirect(request.get_full_path())
            
            success_count = 0
            for user in queryset:
                if user.email:
                    html_message = render_to_string('admin/accounts/user/email_body.html', {
                        'email_message': message,
                        'user_display': user.first_name or user.email,
                    })
                    plain_message = strip_tags(html_message)
                    try:
                        send_mail(
                            subject=subject,
                            message=plain_message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[user.email],
                            html_message=html_message
                        )
                        success_count += 1
                    except Exception as e:
                        messages.error(request, f"Error sending to {user.email}: {e}")
            
            if success_count > 0:
                messages.success(request, f"Successfully sent email to {success_count} users.")
            return redirect(request.get_full_path())

        context = self.admin_site.each_context(request)
        context.update({
            'users': queryset,
            'action': 'send_email_action',
            'opts': self.model._meta,
        })
        return render(request, 'admin/accounts/user/send_email.html', context)

admin.site.unregister(Group) 
@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    readonly_fields = ['name']
    fields = ['name', 'permissions']
    

admin.site.unregister(EmailAddress)
@admin.register(EmailAddress)
class EmailAddressAdmin(ModelAdmin):
    list_display = ['email','name', 'verified', 'primary']
    readonly_fields = ['user'] + list_display

    @display(description="User Name")
    def name(self, obj):
        obj = obj.user
        if not obj.first_name or not obj.last_name:
            return None
        return f"{obj.first_name} {obj.last_name}"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
