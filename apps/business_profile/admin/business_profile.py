from django.contrib import admin
from django.urls import reverse
from unfold.admin import display
from unfold.decorators import action
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.timesince import timesince
from apps.business_profile.models import BusinessProfile, CommentPreset, CommentLog, Customer, WhatsappTemplate
from apps.core.utils import profile_html
from apps.core.admin import ModelAdmin, CustomAdmin
from apps.core.admin.mixins import UserRestrictionMixin, InlinePlacementMixin
from django import forms
import logging

logger = logging.getLogger(__name__)

class CommentPresetForm(forms.ModelForm):
    class Meta:
        model = CommentPreset
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comment_text'].widget.attrs.update({'rows': '4'})
    

@admin.register(BusinessProfile)
class BusinessProfileAdmin(UserRestrictionMixin, InlinePlacementMixin, ModelAdmin):
    list_before_template = "admin/business_profile/businessprofile/list_before.html"
    list_display = ['profile', 'platform', 'last_activity', 'credit_per_reply', 'reply_enabled']
    list_filter = ['platform_name', 'reply_enabled']
    actions_row = ['view_on_platform']
    actions_detail = ['sync_whatsapp_templates', 'view_on_platform']
    search_fields = ['name', 'platform_id', 'user__email', 'user__first_name']
    list_editable = ['reply_enabled']
    readonly_fields = ['last_activity', 'platform_name', 'platform_id', 'profile', 'profile_pic', 'name', 'platform_url', 'api_key_display', 'api_documentation', 'knowledge', 'knowledge_token', 'credit_per_reply', 'user_link', "user_full_name", "user_phone_number", "user_credit_balance"]
    fieldsets = (
        (
            "AI Knowledge",
            {
                "classes": ("tab",),
                "fields": ("system_prompt", "business_info", "order_fields","knowledge_token", "credit_per_reply"),
            }
        ),
        (
            "Settings",
            {
                "classes": ("tab",),
                "fields": ("reply_enabled", "ai_model", "openrouter_api_key", "auto_pause", "pause_timeout",
                           "comments_reply_enabled", "delete_negative_comments"),
            }
        ),
        (
            "Order API & Webhook",
            {
                "classes": ("tab",),
                "fields": ("api_enabled", "api_key_display", "webhook_enabled", "webhook_url", "api_documentation"),
            }
        ),
        (
            "Profile",
            {
                "classes": ("tab",),
                "fields": ("profile", "platform_name", "platform_id", "platform_url"),
            }
        ),
    )

    @display(description="API Key")
    def api_key_display(self, obj):
        if not obj.api_key:
            return "Not generated yet (enable API and save to generate)"
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<input type="password" class="input" id="api_key_field" readonly value="{}"/>'
            '<button type="button" class="btn" onclick="const el = document.getElementById(\'api_key_field\'); el.select(); navigator.clipboard.writeText(el.value); alert(\'Copied to clipboard!\');">Copy</button>'
            '</div>',
            obj.api_key
        )

    @display(description="API Documentation")
    def api_documentation(self, obj):
        return format_html(
            '<a target="_blank" class="text-primary-600 underline" href="{}">{}</a>',
            "/i/order-api-and-webhook/",
            "/i/order-api-and-webhook/"
        )

    @display(description="Profile")
    def profile(self, obj):
        image_url = ''
        if obj.profile_pic:
            image_url = obj.profile_pic.url
        elif obj.platform_name == "facebook":
            image_url = "/static/img/gray_facebook.jpg"
        elif obj.platform_name == "whatsapp":
            image_url = "/static/img/gray_whatsapp.jpg"
        return profile_html(image_url, obj.name)
        
    @display(ordering="platform_name")
    def platform(self, obj):
        return obj.platform_name
    
    @display()
    def last_activity(self, obj):
        latest_conversation = obj.conversations.order_by('-updated_at').first()
        if latest_conversation:
            return timesince(latest_conversation.updated_at) + " ago"
        return "Never"
    
    
    @display(description="View on Platform")
    def platform_url(self, obj):
        if obj.platform_name == "facebook":
            url = f'https://www.facebook.com/{obj.platform_id}'
            return mark_safe(f"<a class='text-primary-600 underline' href='{url}' target='_blank'>{url}</a>")
    ### actions ###
    
    @action(description="View on Platform", icon="link", permissions=["view_on_platform"])
    def view_on_platform(self, request, object_id):
        obj = self.get_object(request, object_id)
        if obj.platform_name == "facebook":
            return redirect(f"https://www.facebook.com/{obj.platform_id}")
        else:
            # send back where he was
            return redirect(request.META.get('HTTP_REFERER'))

    @action(description="Sync Whatsapp Templates", icon="sync", permissions=["sync_whatsapp_templates"])
    def sync_whatsapp_templates(self, request, object_id):
        obj = self.get_object(request, object_id)
        if obj.platform_name != "whatsapp":
            messages.error(request, "Not a WhatsApp account")
            return redirect(request.META.get('HTTP_REFERER'))
            
        try:
            count = obj.sync_whatsapp_templates()
            messages.success(request, f"Successfully synced {count} templates.")
        except Exception as e:
            logger.exception(e)
            messages.error(request, "Somthing went wrong. Please try again")
        return redirect(request.META.get('HTTP_REFERER'))

    def has_add_permission(self, request):
        return False
    
    def has_sync_whatsapp_templates_permission(self, request, object_id=None):
        obj = self.get_object(request, object_id)
        if obj and obj.platform_name == "whatsapp":
            return True
        return False
    
    def has_view_on_platform_permission(self, request, object_id=None):
        obj = self.get_object(request, object_id)
        if obj and obj.platform_name == "facebook":
            return True
        return False

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        source_model = request.GET.get('model_name')
        source_field = request.GET.get('field_name')
        # filter by platform if source model is commentpreset
        if source_model == 'commentpreset' and source_field == 'business_profile':
            queryset = queryset.filter(platform_name='facebook')
            
        return queryset, use_distinct
    
    @display(description="User")
    def user_link(self, obj):
        if obj.user:
            return format_html(
                '<a class="text-primary-600 underline" href="{}">{}</a>',
                reverse('admin:accounts_user_change', args=[obj.user.id]),
                escape(obj.user.email)
            )
        return "-"
    
    def user_full_name(self, obj):
        return obj.user.full_name
    
    def user_phone_number(self, obj):
        return obj.user.phone_number
    
    def user_credit_balance(self, obj):
        return obj.user.credit_balance
    
    def get_list_display(self, request):
        display = list(super().get_list_display(request))
        if request.user.is_superuser and 'user_link' not in display:
            display.insert(1, 'user_link')
        return display
    
    def get_fieldsets(self, request, obj = None):
        fs = super().get_fieldsets(request, obj)
        if request.user.is_superuser and not any(f[0] == "User" for f in fs):
            fs += (
                (
                    "User",
                    {
                        "classes": ("tab",),
                        "fields": ("user_link", "user_full_name", "user_phone_number", "user_credit_balance"),
                    }
                ),
            )
        return fs
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser and 'ai_model' not in readonly_fields:
            readonly_fields.append('ai_model')
        return readonly_fields
        

         
@admin.register(Customer)
class CustomerAdmin(UserRestrictionMixin, ModelAdmin):
    user_field = "business_profile.user"
    list_display = ['id', 'platform_id', 'name', 'gender']

    def has_add_permission(self, request, *args, **kwargs):
        return False
