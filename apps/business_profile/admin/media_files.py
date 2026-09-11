from apps.business_profile.models import MediaFiles
from django.contrib import admin
from unfold.admin import display
from apps.core.utils import image_html
from apps.core.admin import ModelAdmin
from apps.core.admin.mixins import UserRestrictionMixin
from .filteres import BusinessProfileFilter


@admin.register(MediaFiles)
class MediaFilesAdmin(UserRestrictionMixin, ModelAdmin):
    user_field = "business_profile.user"
    list_display = ('preview', 'business_profile', 'file', 'file_type', 'is_active')
    autocomplete_fields = ['product', 'business_profile']
    list_filter = [BusinessProfileFilter, 'file_type', 'is_active']
    list_editable = ['is_active']
    search_fields = ['transcription', 'business_profile__name', 'product__title']
    readonly_fields = ['preview']
    fields = ('business_profile', 'file', 'transcription')
    
    @display(description="Preview")
    def preview(self, obj):
        url = None
        if obj.file_type=='image':
            url = obj.file.url
        return image_html(url, alt="No+Preview")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(product__isnull=True)
