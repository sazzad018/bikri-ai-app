import types
from django.contrib import admin
from django import forms
from unfold.admin import display
from django.utils.html import format_html
from import_export import resources, fields
from import_export.admin import ExportActionModelAdmin
from unfold.contrib.import_export.forms import SelectableFieldsExportForm

from apps.business_profile.models import Order, BusinessProfile
from apps.core.admin import ModelAdmin
from apps.core.utils import profile_html
from apps.core.admin.mixins import UserRestrictionMixin
from .filteres import BusinessProfileFilter


class OrderAddForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['business_profile', 'conversation', 'fields']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['conversation'].required = False
        
        if self.user and not self.user.is_superuser:
            self.fields['business_profile'].queryset = BusinessProfile.objects.filter(user=self.user)
            self.fields['conversation'].queryset = self.fields['conversation'].queryset.filter(business_profile__user=self.user).order_by('-updated_at', '-created_at')

    def clean(self):
        cleaned_data = super().clean()
        business_profile = cleaned_data.get('business_profile')
        conversation = cleaned_data.get('conversation')
        
        if conversation and business_profile:
            if conversation.business_profile != business_profile:
                self.add_error(
                    'conversation',
                    "The selected conversation does not belong to the selected business profile."
                )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.customer and instance.conversation:
            instance.customer = instance.conversation.customer
        if commit:
            instance.save()
        return instance


@admin.register(Order)
class OrderAdmin(UserRestrictionMixin, ModelAdmin, ExportActionModelAdmin):
    user_field = "business_profile.user"
    list_display = ['customer_profile', 'business_profile', 'id', 'status', 'date_time']
    list_editable = ['status']
    list_filter = [BusinessProfileFilter, 'created_at', 'updated_at']
    search_fields = ['customer__name', 'id', 'business_profile__name', 'fields']
    fields = ['business_profile', 'customer_profile', 'status', 'fields', 'created_at', 'updated_at']
    readonly_fields = ['customer_profile', 'created_at', 'updated_at']
    add_form = OrderAddForm
    add_fields = ['business_profile', 'conversation', 'fields']

    export_form_class = SelectableFieldsExportForm

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ['customer_profile', 'created_at', 'updated_at']
        return ['business_profile', 'customer_profile', 'created_at', 'updated_at']

    def get_form(self, request, obj=None, change=False, **kwargs):
        if obj is None:
            FormClass = self.add_form
            user = request.user

            class UserScopedOrderAddForm(FormClass):
                def __init__(self_, *args, **fkwargs):
                    fkwargs.setdefault('user', user)
                    super().__init__(*args, **fkwargs)

            kwargs['form'] = UserScopedOrderAddForm
            kwargs.setdefault('fields', self.add_fields)
        return super().get_form(request, obj, change=change, **kwargs)

    def get_fields(self, request, obj=None):
        if obj is None:
            return self.add_fields
        return super().get_fields(request, obj)

    @display(description='Customer Profile',  ordering="customer__name")
    def customer_profile(self, obj):
        if not obj.customer:
            return "-"
        if obj.customer.profile_pic:
            return profile_html(obj.customer.profile_pic.url, obj.customer.name)
        return profile_html("", obj.customer.name)
    
    @display(description="Date Time", ordering="created_at")
    def date_time(self, obj):
        return  format_html('<pre class="pr-4 max-w-xl truncate">{}</pre>', obj.created_at.strftime("%d/%m/%y %H:%M"))
    
    def get_list_display(self, request):
        base_list_display = list(super().get_list_display(request))
        
        if request.user.is_superuser:
            business_profiles = BusinessProfile.objects.all()
        else:
            business_profiles = request.user.business_profiles.all()

        dynamic_fields = []
        for bp in business_profiles:
            if bp.order_fields_list:
                for field in bp.order_fields_list:
                    if field not in dynamic_fields:
                        dynamic_fields.append(field)
        
        for field_name in dynamic_fields:
            if not hasattr(self, field_name):
                raw_getter = self._create_dynamic_field_getter(field_name)
                bound_getter = types.MethodType(raw_getter, self)
                setattr(self, field_name, bound_getter)
                
        return base_list_display + dynamic_fields

    def _create_dynamic_field_getter(self, field_name):
        @display(description=field_name.replace('_', ' ').title())
        def dynamic_getter(self, obj):
            if obj.fields and isinstance(obj.fields, dict):
                data = obj.fields.get(field_name, "-")
                return format_html('<pre class="pr-4 max-w-xl truncate">{}</pre>', data)
            return "-"
        return dynamic_getter

    def get_export_resource_classes(self, request):
        """
        Dynamically generates the export Resource class matching 
        the user's exact list_display configuration.
        """
        list_display_fields = self.get_list_display(request)
        attrs = {}

        # 1. Define base model attributes as text (stripping HTML formatting for export)
        if 'id' in list_display_fields:
            attrs['id'] = fields.Field(attribute='id', column_name='ID')

        if 'business_profile' in list_display_fields:
            attrs['business_profile'] = fields.Field(attribute='business_profile', column_name='Business Profile')

        if 'customer_profile' in list_display_fields:
            attrs['customer_profile'] = fields.Field(column_name='Customer Profile')
            def dehydrate_customer_profile(self, obj):
                return obj.customer.name if getattr(obj, 'customer', None) else "-"
            attrs['dehydrate_customer_profile'] = dehydrate_customer_profile

        if 'date_time' in list_display_fields:
            attrs['date_time'] = fields.Field(column_name='Date Time')
            def dehydrate_date_time(self, obj):
                return obj.created_at.strftime("%d/%m/%y %H:%M") if getattr(obj, 'created_at', None) else "-"
            attrs['dehydrate_date_time'] = dehydrate_date_time

        # 2. Define JSON Dynamic Attributes
        base_fields = ['customer_profile', 'business_profile', 'id', 'date_time']
        dynamic_json_fields = [f for f in list_display_fields if f not in base_fields]

        for field_name in dynamic_json_fields:
            attrs[field_name] = fields.Field(column_name=field_name.replace('_', ' ').title())

            # Create a closure so each function retains its specific field_name reference
            def make_dehydrate(fname):
                def dehydrate_func(self, obj):
                    if obj.fields and isinstance(obj.fields, dict):
                        return obj.fields.get(fname, "-")
                    return "-"
                return dehydrate_func

            attrs[f'dehydrate_{field_name}'] = make_dehydrate(field_name)

        # 3. Create Meta configuration
        class Meta:
            model = Order
            fields = list_display_fields
            export_order = list_display_fields

        attrs['Meta'] = Meta

        # 4. Dynamically assemble and return the Resource class
        DynamicOrderResource = type('DynamicOrderResource', (resources.ModelResource,), attrs)
        return [DynamicOrderResource]