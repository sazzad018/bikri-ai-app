from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.business_profile.models import BusinessProfile, Product, MediaFiles
from apps.core.models.private import SiteConfig
import logging

logger = logging.getLogger(__name__)

# signal to set default values for new BusinessProfile instances when created from SiteConfig
@receiver(post_save, sender=BusinessProfile)
def set_default_business_profile_values(sender, instance, created, **kwargs):
    if created:
        siteconfig = SiteConfig.objects.first()
        if siteconfig:
            instance.system_prompt = siteconfig.default_system_prompt
            instance.business_info = siteconfig.default_business_info
            instance.ai_model = siteconfig.default_ai_model
            instance.save(update_fields=["system_prompt", "business_info", "ai_model"])

@receiver((post_save, post_delete), sender=Product)
@receiver((post_save, post_delete), sender=MediaFiles)
@receiver(post_save, sender=BusinessProfile)
def update_knowledge(sender, instance, **kwargs):
    if sender == BusinessProfile:
        business_profile = instance
    else:
        business_profile = instance.business_profile

    if business_profile:
        business_profile.update_knowledge()

