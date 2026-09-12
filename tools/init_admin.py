import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User
from django.contrib.sites.models import Site
from apps.core.models.private import SiteConfig
from allauth.account.models import EmailAddress

# 1. Initialize Site
try:
    site_domain = os.environ.get('SITE_DOMAIN', 'bikri-ai-app.onrender.com')
    site, _ = Site.objects.get_or_create(id=1)
    site.domain = site_domain
    site.name = "Cholbe AI"
    site.save()
    print(f"==> Configured Site domain: {site_domain}")
except Exception as e:
    print(f"==> Warning: Could not configure Site: {e}")

# 2. Initialize SiteConfig
try:
    SiteConfig.get_solo()
    print("==> SiteConfig verified/initialized.")
except Exception as e:
    print(f"==> Warning: Could not initialize SiteConfig: {e}")

# 3. Create or update superuser
admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
admin_password = os.environ.get('ADMIN_PASSWORD', 'Admin@123456')

if admin_email and admin_password:
    user = User.objects.filter(email=admin_email).first()
    if not user:
        user = User.objects.create_superuser(email=admin_email, password=admin_password)
        print(f"==> Successfully created superuser: {admin_email}")
    else:
        user.set_password(admin_password)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
        print(f"==> Superuser already exists. Credentials updated for: {admin_email}")

    try:
        email_obj, _ = EmailAddress.objects.get_or_create(
            user=user,
            email=admin_email,
            defaults={'verified': True, 'primary': True}
        )
        if not email_obj.verified or not email_obj.primary:
            email_obj.verified = True
            email_obj.primary = True
            email_obj.save()
            print(f"==> Verified allauth EmailAddress for: {admin_email}")
    except Exception as e:
        print(f"==> Warning: Could not verify EmailAddress: {e}")
else:
    print("==> ADMIN_EMAIL or ADMIN_PASSWORD missing. Skipping superuser creation.")

# 4. Verify all existing users' emails to prevent login block
try:
    for u in User.objects.all():
        e_obj, _ = EmailAddress.objects.get_or_create(
            user=u,
            email=u.email,
            defaults={'verified': True, 'primary': True}
        )
        if not e_obj.verified:
            e_obj.verified = True
            e_obj.save()
except Exception as e:
    print(f"==> Warning: Could not verify all user emails: {e}")
