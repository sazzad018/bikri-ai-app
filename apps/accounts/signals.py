from django.db.models.signals import post_save
from allauth.account.signals import user_signed_up, user_logged_out
from django.dispatch import receiver
from apps.accounts.models import User
from apps.core.models import SiteConfig
from django.contrib.auth.models import Group
from django.contrib import messages

@receiver(post_save, sender=User)
def assign_default_group(sender, instance, created, **kwargs):
    if created:
        group, _ = Group.objects.get_or_create(name='standard_users')
        instance.groups.add(group)

@receiver(user_signed_up)
def on_user_signed_up(request, user, **kwargs):

    siteconfig = SiteConfig.get_solo()
    free_credits_amount = siteconfig.free_credits_on_signup
    user.credit_transaction(free_credits_amount, "free")
    
    if request:
        request.session['gtm_signup'] = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone_number,
            'timestamp': user.date_joined.timestamp() if user.date_joined else None,
        }
    
    messages.success(
        request, 
        f"Welcome! You have been given {free_credits_amount} free credits to test our service."
    )

@receiver(user_logged_out)
def on_user_logout(request, user, **kwargs):
    if request:
        request.session['gtm_logout'] = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone_number,
            'timestamp': user.date_joined.timestamp() if user.date_joined else None,
        }