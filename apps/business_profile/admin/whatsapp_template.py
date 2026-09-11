from django.contrib import admin
from unfold.admin import display
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.template.loader import render_to_string
from apps.business_profile.models import WhatsappTemplate
from apps.core.admin import ModelAdmin
from apps.core.admin.mixins import UserRestrictionMixin
from apps.business_profile.models import BusinessProfile
from .filteres import BusinessProfileFilter



class WhatsappBusinessProfileFilter(BusinessProfileFilter):
    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return BusinessProfile.objects.filter(platform_name='whatsapp').values_list('id', 'name').order_by('name')
        else:
            return BusinessProfile.objects.filter(user=request.user, platform_name='whatsapp').values_list('id', 'name').order_by('name')

@admin.register(WhatsappTemplate)
class WhatsappTemplateAdmin(UserRestrictionMixin, ModelAdmin):
    user_field = "business_profile.user"
    list_display = ['template_id', 'business_profile', 'name', 'language', 'status', 'category']
    list_filter = [WhatsappBusinessProfileFilter, 'language', 'status', 'category']
    search_fields = ['template_id', 'name', 'business_profile__name', 'components']
    fields = [('business_profile', 'template_id'), ('name', 'language'), ('status', 'category'), 'template_preview']

    def has_add_permission(self, request, *args, **kwargs):
        
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

    @display()
    def template_preview(self, obj):
        # render admin/business_profile/conversation/whatsapp_template_preview.html this template with passing component to it

        msg_bubble = render_to_string('admin/business_profile/conversation/whatsapp_template_preview.html', {'components': obj.components})

        return format_html(
            "<div class='bg-stone-100 p-4 rounded-2xl flex items-center justify-center'>{}</div>", msg_bubble
        )