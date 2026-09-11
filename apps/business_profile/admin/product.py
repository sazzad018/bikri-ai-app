from django.contrib import admin
from django import forms
from django.utils.html import format_html
from unfold.admin import TabularInline, display
from apps.business_profile.models import Product, MediaFiles, BusinessProfile
from apps.core.utils import guess_file_type, image_html
from apps.core.admin import ModelAdmin
from apps.core.admin.mixins import UserRestrictionMixin
from .filteres import BusinessProfileFilter

from import_export import resources, fields
from import_export.admin import ImportExportActionModelAdmin
from import_export.forms import ConfirmImportForm
from unfold.contrib.import_export.forms import ImportForm, SelectableFieldsExportForm
from unfold.widgets import UnfoldAdminSelectWidget


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        fields = ('title', 'description', 'price', 'is_active')
        import_id_fields = ()

    def before_save_instance(self, instance, row, **kwargs):
        business_profile_id = kwargs.get("business_profile_id")
        if business_profile_id:
            instance.business_profile_id = business_profile_id

class ProductImportForm(ImportForm):
    business_profile = forms.ModelChoiceField(
        queryset=BusinessProfile.objects.all(),
        required=True,
        widget=UnfoldAdminSelectWidget()
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request and not self.request.user.is_superuser:
            self.fields['business_profile'].queryset = self.request.user.business_profiles.all()


class ProductConfirmImportForm(ConfirmImportForm):
    business_profile = forms.ModelChoiceField(
        queryset=BusinessProfile.objects.all(),
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request and not self.request.user.is_superuser:
            self.fields['business_profile'].queryset = self.request.user.business_profiles.all()


class MediaFileForm(forms.ModelForm):
    class Meta:
        model = MediaFiles
        fields = ('file', 'transcription')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['transcription'].widget.attrs.update({'rows': '2'})

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Ensure business_profile is synced from the parent product
        if hasattr(self.instance, 'product') and self.instance.product:
            instance.business_profile = self.instance.product.business_profile
            instance.file_type = guess_file_type(instance.file.url)

        if commit:
            instance.save()
        return instance

class FileInline(TabularInline):
    model = MediaFiles
    form = MediaFileForm
    extra = 0
    ordering_field = 'priority'
    hide_ordering_field = True
    fields = ( 'preview', 'file', 'transcription', 'priority', 'is_active')
    readonly_fields = ('preview',)
    hide_title = True
    tab = True
    template = "admin/business_profile/edit_inline/tabular.html"
    per_page = 10
    
    @display(description="Image")
    def preview(self, obj):
        if obj.file_type=='image':
            return image_html(obj.file.url)
        # return "No Image"

@admin.register(Product)
class ProductAdmin(UserRestrictionMixin, ModelAdmin, ImportExportActionModelAdmin):
    resource_class = ProductResource
    import_form_class = ProductImportForm
    confirm_form_class = ProductConfirmImportForm
    export_form_class = SelectableFieldsExportForm

    change_list_template = "admin/business_profile/product/change_list_cards.html"

    user_field = "business_profile.user"
    inlines = [FileInline]
    list_display = [ 'title', 'business_profile', 'price', 'is_active']
    autocomplete_fields = ['business_profile']
    search_fields = ["title", "description", "business_profile__name"]
    list_filter = [BusinessProfileFilter, 'is_active', 'updated_at', 'created_at']
    list_per_page = 20

    def get_import_form_kwargs(self, request):
        kwargs = super().get_import_form_kwargs(request)
        kwargs['request'] = request
        return kwargs

    def get_confirm_form_kwargs(self, request, import_form=None):
        kwargs = super().get_confirm_form_kwargs(request, import_form)
        kwargs['request'] = request
        return kwargs

    def get_import_data_kwargs(self, *args, **kwargs):
        kw = super().get_import_data_kwargs(*args, **kwargs)
        form = kwargs.get("form")
        if form and hasattr(form, "cleaned_data"):
            bp = form.cleaned_data.get("business_profile")
            if bp:
                kw["business_profile_id"] = bp.pk
        return kw

    def get_confirm_form_initial(self, request, import_form):
        initial = super().get_confirm_form_initial(request, import_form)
        if import_form:
            initial["business_profile"] = import_form.cleaned_data.get("business_profile")
        return initial
    