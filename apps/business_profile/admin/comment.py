from apps.business_profile.models import CommentPreset, CommentLog
from django.contrib import admin
from unfold.admin import display
from apps.core.admin import ModelAdmin
from apps.core.admin.mixins import UserRestrictionMixin
from apps.business_profile.admin.filteres import BusinessProfileFilter
from apps.core.utils import profile_html

@admin.register(CommentPreset)
class CommentPresetAdmin(UserRestrictionMixin, ModelAdmin):
    user_field = "business_profile.user"
    list_display = ['keywords_display', 'comment_text', 'reply_destination', 'business_profile']
    search_fields = ['keywords', 'comment_text', 'business_profile__name']
    autocomplete_fields = ['business_profile']
    list_filter = [BusinessProfileFilter, 'created_at', 'updated_at']

    @display(description="Keywords")
    def keywords_display(self, obj):
        return ", ".join(obj.keywords)

@admin.register(CommentLog)
class CommentLogAdmin(UserRestrictionMixin, ModelAdmin):
    user_field = "business_profile.user"
    list_display = ['customer_profile', 'business_profile', 'comment_text', 'reply_text', 'sentiment_score']
    readonly_fields = list_display
    fields = list_display
    search_fields = ['customer__name', 'comment_text', 'reply_text', 'business_profile__name']
    list_filter = [BusinessProfileFilter, 'created_at', 'updated_at']
    def has_add_permission(self, request, *args, **kwargs):
        return False

    def has_change_permission(self, request, obj=None):
        return False
    
    @display(description="Customer Profile", ordering="psid")
    def customer_profile(self, obj):
        print(obj)
        customer = obj.business_profile.customers.filter(platform_id=obj.psid).first()
        if customer:
            image_url = customer.profile_pic.url if customer.profile_pic else ''
            return profile_html(image_url, customer.name)
        return obj.psid