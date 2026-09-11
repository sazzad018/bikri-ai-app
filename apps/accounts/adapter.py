import secrets
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    def generate_email_verification_code(self):
        return str(secrets.randbelow(900000) + 100000)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        if not user.first_name:
            user.first_name = data.get('first_name') or data.get('name', '').split()[0] if data.get('name') else ''
        if not user.last_name:
            name_parts = data.get('name', '').split()
            user.last_name = data.get('last_name') or (' '.join(name_parts[1:]) if len(name_parts) > 1 else '')

        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        extra_data = sociallogin.account.extra_data
        picture_url = None
        if sociallogin.account.provider == 'google':
            picture_url = extra_data.get('picture')

        if picture_url and request:
            request.session['social_picture_url'] = picture_url

        return user