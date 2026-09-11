from django.contrib import admin
from unfold.admin import TabularInline, display
from django.utils.html import format_html
from apps.core.models import SiteConfig, InfoPage, HomePage, HomePageSection, GalleryItem, Popup
from apps.credit.models import CreditPackage
from django.contrib.sites.models import Site
from apps.core.utils import image_html
from .mixins import ModelAdmin


class CreditPackageInline(TabularInline):
    model = CreditPackage
    extra = 0
    tab = True
    ordering_field = 'order'
    hide_ordering_field = True
    hide_title = True

@admin.register(SiteConfig)
class SiteConfigAdmin(ModelAdmin):
    inlines = [CreditPackageInline]
    
    def has_add_permission(self, request):
        return not SiteConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(InfoPage)
class InfoPageAdmin(ModelAdmin):
    list_display = ('slug', 'title', 'url')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')

    @display(description="URL")
    def url(self, obj):
        return format_html('<a target="_blank" class="text-primary-600 underline" href="{}">{}</a>', obj.get_url(), obj.get_url())

class HomePageSectionInline(TabularInline):
    model = HomePageSection
    ordering_field = 'order'
    hide_ordering_field = True
    hide_title = True
    fields = ('html', 'is_active')
    extra = 1
    tab = True

@admin.register(HomePage)
class HomePageAdmin(ModelAdmin):
    inlines = [HomePageSectionInline]
    fieldsets = (
        ("SEO", {
            "fields": ("title", "meta_description", "meta_keywords", "extra_head"),
            "classes": ("tab",)
        }),
        ("Hero Section", {
            "fields": ("hero_tag", "hero_title", "hero_subtitle", "see_demo_url", "support_whatsapp_number"),
            "classes": ("tab",)
        }),
        ("Phone Chat", {
            "fields": ("phone_chat",),
            "classes": ("tab",)
        }),
        ("Reviews Section", {
            "fields": ("reviews_title", "reviews_subtitle", "reviews"),
            "classes": ("tab",)
        }),
        ("FAQ Section", {
            "fields": ("faq_title", "faqs"),
            "classes": ("tab",)
        }),
        ("Footer Section", {
            "fields": ("footer_text", "social_links", "link_groups"),
            "classes": ("tab",)
        })



    )
    def has_add_permission(self, request):
        return not HomePage.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(GalleryItem)
class GalleryItemAdmin(ModelAdmin):
    list_display = ("title", "preview", "file_url", "uploaded_at")
    search_fields = ("title", "file")
    readonly_fields = ("uploaded_at", "file_url", "preview")

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    @display(description="Preview")
    def preview(self, obj):
        if obj.file:
            ext = obj.file.name.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp']:
                return image_html(obj.file.url)
        return "No Preview"

    @display(description="File URL")
    def file_url(self, obj):
        if obj.file:
            url = obj.file.url
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<input type="text" readonly value="{}" style="padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 12px; width: 350px; background: #f9f9f9; color: #333;" onclick="this.select(); navigator.clipboard.writeText(this.value); alert(\'Copied to clipboard!\');" />'
                '<a href="{}" target="_blank" class="text-primary-600 underline" style="font-size: 12px;">View</a>'
                '</div>',
                url, url
            )
        return "-"
    
@admin.register(Popup)
class PopupAdmin(ModelAdmin):
    list_display = ('name', 'read_count')
    filter_horizontal = ['users', 'users_read']
    readonly_fields = ['read_count', 'users_read']

    fieldsets = (
        ('Popup', {
            'fields': ('name', 'content', 'buttons'),
            'classes': ('tab',)
        }),
        ('Audience', {
            'fields': ('users', 'users_read'),
            'classes': ('tab',)
        })
    )

    
    @display(description="Read Count")
    def read_count(self, obj):
        return obj.users_read.count()

admin.site.unregister(Site)
@admin.register(Site)
class SiteAdmin(ModelAdmin):
    list_display = ('domain', 'name')