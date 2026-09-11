from django.apps import AppConfig


class BusinessProfileConfig(AppConfig):
    name = 'apps.business_profile'

    def ready(self):
        import apps.business_profile.signals
