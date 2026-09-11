from django.contrib import admin
from apps.business_profile.models import BusinessProfile

class BusinessProfileFilter(admin.SimpleListFilter):
    title = 'Business Profile'
    parameter_name = 'business_profile'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return BusinessProfile.objects.all().values_list('id', 'name').order_by('-updated_at', '-created_at')[:10]
        else:
            return BusinessProfile.objects.filter(user=request.user).values_list('id', 'name').order_by('-updated_at', '-created_at')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(business_profile=self.value())
        
    def has_output(self):
        if self.lookup_choices is None:
            return False
        return len(self.lookup_choices) > 1