from django.contrib import admin
from functools import reduce
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django_jsonform.models.fields import JSONField
from unfold.admin import ModelAdmin as BaseModelAdmin

class CustomAdmin():
    warn_unsaved_form = True
    def response_change(self, request, obj):
        if "_continue" not in request.POST and "_addanother" not in request.POST:
            return redirect(request.path)
        
        return super().response_change(request, obj)
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, JSONField):
            return db_field.formfield(**kwargs)
        
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    
class ModelAdmin(CustomAdmin, BaseModelAdmin):
    pass

class UserRestrictionMixin:
    user_field: str = "user" 

    def _get_obj_user(self, obj):
        """Traverse dotted path to retrieve the user from the object."""
        try:
            return reduce(getattr, self.user_field.split("."), obj)
        except AttributeError:
            return None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Convert dot notation to Django ORM lookup: "profile.user" -> "profile__user"
        lookup = self.user_field.replace(".", "__")
        return qs.filter(**{lookup: request.user})

    def _check_object_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.is_superuser:
            return True
        return self._get_obj_user(obj) == request.user
    
    def has_add_permission(self, request, *args, **kwargs):
        return self._check_object_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._check_object_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self._check_object_permission(request, obj)

    def has_view_permission(self, request, obj=None):
        return self._check_object_permission(request, obj)


class AdminReadonlyMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
from django.utils.safestring import mark_safe

class InlinePlacementMixin:
    """
    A mixin for Django Unfold that allows you to seamlessly embed inlines 
    directly inside fieldsets using placeholder fields.
    """
    inline_placeholders = {}

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        for placeholder, inline_id in getattr(self, 'inline_placeholders', {}).items():
            setattr(self, placeholder, self._create_placeholder_method(inline_id))

    def _create_placeholder_method(self, inline_target_id):
        def placeholder_method(obj=None):
            return mark_safe(f"""
                <div id="anchor-{inline_target_id}" style="display: none;"></div>
                <script>
                    window.addEventListener('load', function() {{
                        const inlineEl = document.getElementById('{inline_target_id}');
                        const anchorEl = document.getElementById('anchor-{inline_target_id}');

                        if (!anchorEl) console.warn(`Anchor element for inline '{inline_target_id}' not found.`);
                        if (!inlineEl) console.warn(`Inline element for inline '{inline_target_id}' not found.`);

                        if (inlineEl && anchorEl) {{
                            // Find the wrapper field row (typically '.form-row' in Django/Unfold)
                            const fieldRow = anchorEl.closest('.form-row') || anchorEl.parentElement;
                            
                            // Move the inline element right before the placeholder row
                            fieldRow.parentNode.insertBefore(inlineEl, fieldRow);
                            
                            // Hide the placeholder row entirely so it doesn't leave an empty gap
                            fieldRow.style.display = 'none';
                            
                            // Hide
                            inlineEl.querySelector('h2').style.display = 'none';
                            inlineEl.querySelector('.formset-wrapper').style.border = 'none';
                        }}
                    }});
                </script>
            """)
        
        placeholder_method.short_description = "" 
        return placeholder_method

    def get_readonly_fields(self, request, obj=None):
        ro_fields = list(super().get_readonly_fields(request, obj))
        for placeholder in getattr(self, 'inline_placeholders', {}).keys():
            if placeholder not in ro_fields:
                ro_fields.append(placeholder)
        return ro_fields