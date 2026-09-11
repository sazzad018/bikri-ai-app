from apps.business_profile.models import Conversation
from django.contrib import admin
import json
import re
from pywa import WhatsApp
from pywa.types.templates import TemplateLanguage
from django.utils import timezone
from unfold.admin import display
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from django.utils.timesince import timesince
from apps.core.utils import profile_html
from apps.core.admin import ModelAdmin
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from unfold.decorators import action
from unfold.widgets import UnfoldAdminSelectWidget
from apps.business_profile.models import WhatsappTemplate
from apps.core.admin.mixins import UserRestrictionMixin
from .filteres import BusinessProfileFilter

class SendTemplateForm(forms.Form):
    template_id = forms.ChoiceField(
        label="Choose WhatsApp Template",
        choices=[],
        widget=UnfoldAdminSelectWidget(attrs={'class': 'w-full max-w-md'})
    )

    def __init__(self, *args, **kwargs):
        templates = kwargs.pop('templates', [])
        super().__init__(*args, **kwargs)
        self.fields['template_id'].choices = [
            (t.id, f"{t.name} ({t.language}) [{t.category}]") for t in templates
        ]


@admin.register(Conversation)
class ConversationAdmin(UserRestrictionMixin, ModelAdmin):
    user_field = 'business_profile.user'
    list_display = ['user', 'business_profile', 'platform', 'last_activity', 'message_counts', 'credit_used', 'reply_enabled']
    list_editable = ['reply_enabled']
    readonly_fields = ['user', 'render_conversation', 'message_counts', 'credit_used', 'created_at', 'updated_at']
    list_filter = [BusinessProfileFilter, 'business_profile__platform_name', 'reply_enabled', 'updated_at', 'created_at']
    search_fields = ['customer__name', 'json', 'id', 'business_profile__name']
    actions = ['send_wa_template']

    fieldsets = [(None,{'fields': ['user','reply_enabled', 'message_counts', 'credit_used', 'render_conversation', 'created_at', 'updated_at']}),
                 ("json", { 'fields': ['json'], 'classes': ['collapse'] })]
    
    @action(description="Send WhatsApp Template")
    def send_wa_template(self, request, queryset):
        # Filter the queryset to only include WhatsApp conversations
        valid_queryset = queryset.filter(business_profile__platform_name='whatsapp')
        if not valid_queryset.exists():
            messages.error(request, "Selected conversations must be WhatsApp conversations.")
            return redirect(request.get_full_path())
            
        templates = WhatsappTemplate.objects.filter(business_profile__in=valid_queryset.values('business_profile')).distinct()
        
        if 'apply' in request.POST:
            template_id = request.POST.get('template_id')
            if not template_id:
                messages.error(request, "Please select a WhatsApp template.")
                return redirect(request.get_full_path())

            template = WhatsappTemplate.objects.filter(id=template_id).first()
            if not template:
                messages.error(request, "Template not found.")
                return redirect(request.get_full_path())
                
            # Extract variables from the BODY component
            body_text = ""
            for comp in template.components or []:
                if comp.get('type') == 'BODY':
                    body_text = comp.get('text', '')
                    break

            placeholder_pattern = re.compile(r'\{\{(\d+)\}\}')
            matches = placeholder_pattern.findall(body_text)
            variables = sorted(list(set(int(m) for m in matches)))
            
            success_count = 0
            for conv in valid_queryset:
                try:
                    # Build resolved parameters for this customer
                    body_parameters = []
                    for var_num in variables:
                        var_type = request.POST.get(f"var_{var_num}_type", "custom")
                        var_val = request.POST.get(f"var_{var_num}_value", "")
                        
                        resolved_val = var_val
                        now = timezone.localtime()
                        var_type_map = {
                            "customer_name": conv.customer.name,
                            "customer_phone": conv.customer.platform_id,
                            "business_name": conv.business_profile.name,
                            "current_date": now.strftime("%d %B, %Y"),
                            "current_time": now.strftime("%I:%M %p"),
                        }
                        
                        if var_type_map.get(var_type):
                            resolved_val = var_type_map[var_type]
                            
                        body_parameters.append({
                            "type": "text",
                            "text": resolved_val
                        })
                        
                    params_for_send = []
                    if body_parameters:
                        params_for_send.append({
                            "type": "BODY",
                            "parameters": body_parameters
                        })

                    client = WhatsApp(
                        phone_id=conv.business_profile.platform_id, 
                        token=conv.business_profile.platform_access_token
                    )
                    res = client.send_template(
                        to=conv.customer.platform_id,
                        name=template.name,
                        language=TemplateLanguage(template.language),
                        params=params_for_send if params_for_send else None,
                    )
                    conv.add_message(
                        mid=getattr(res, "id", "mid"),
                        role="assistant",
                        content=f"[Template Sent: {template.name}]"
                    )
                    conv.json = conv.get_json() + [{"role": "assistant", "content": f"[Template Sent: {template.name}]"}]
                    conv.save()
                    success_count += 1
                except Exception as e:
                    err_msg = str(e.message)
                    print(err_msg)
                    if "TemplateNotExists" in type(e).__name__ or "132001" in err_msg:
                        friendly_err = "Template does not exist or was created recently. Please wait some time and try again."
                        messages.error(request, f"Error sending to {conv.customer.name}: {friendly_err}")
                    else:
                        messages.error(request, f"Error sending to {conv.customer.name}: {err_msg}")
            
            if success_count > 0:
                messages.success(request, f"Successfully sent template to {success_count} conversations.")
            return redirect(request.get_full_path())
        else:
            form = SendTemplateForm(templates=templates)
            
        context = self.admin_site.each_context(request)
        context.update({
            'conversations': valid_queryset,
            'form': form,
            'action': 'send_wa_template',
            'opts': self.model._meta,
            'templates': templates,
        })
        return render(request, 'admin/business_profile/conversation/send_template.html', context)
    
    @display
    def user(self, obj, ordering="customer__name"):
        image_url = ''
        if obj.customer.profile_pic:
            image_url = obj.customer.profile_pic.url
        return profile_html(image_url, obj.customer.name)
    
    @display(description="Platform", ordering="business_profile__platform_name")
    def platform(self, obj):
        return obj.business_profile.platform_name
    
    @display(description="Conversation")
    def render_conversation(self, obj):
        conversation = obj.get_json()
        if not conversation:
            return mark_safe("<span class='text-gray-500'>No conversation data available.</span>")

        # Safely dump and escape the JSON to pass it into the HTML attribute
        json_data = escape(json.dumps(conversation))

        # Alpine.js will automatically parse the escaped JSON inside x-data
        html = f"""
        <div x-data='{{ messages: {json_data} }}' 
             class="flex flex-col space-y-4 p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg font-sans w-full min-w-[300px]">
            
            <template x-for="(msg, index) in messages" :key="index">
                <div class="flex flex-col w-full" :class="msg.role === 'user' ? 'items-end' : 'items-start'">
                    
                    <div class="max-w-[85%] sm:max-w-[70%] px-3 py-2 rounded-[6px] shadow-xs text-sm"
                         :class="msg.role === 'user' 
                            ? 'bg-primary-600 text-white rounded-br-none' 
                            : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-bl-none border border-gray-100 dark:border-gray-700'">
                        <p class="whitespace-pre-wrap break-words font-medium leading-relaxed" x-text="msg.content"></p>
                    </div>

                    <template x-if="msg.quick_replies && msg.quick_replies.length > 0">
                        <div class="flex flex-wrap gap-1.5 mt-2 max-w-[85%] sm:max-w-[70%]" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
                            <template x-for="qr in msg.quick_replies">
                                <span class="px-2.5 py-1 text-[11px] font-semibold tracking-wide bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded whitespace-nowrap cursor-default" 
                                      x-text="qr"></span>
                            </template>
                        </div>
                    </template>
                    
                </div>
            </template>
            
            <template x-if="messages.length === 0">
                <div class="text-center text-gray-500 dark:text-gray-400 py-4 text-sm">
                    No messages in this conversation yet.
                </div>
            </template>
        </div>
        """
        return mark_safe(html)
    
    @display
    def last_activity(self, obj):
        return timesince(obj.updated_at) + " ago"
    
    @display
    def message_counts(self, obj):
        return f"User: {obj.messages.filter(role='user').count()} | AI: {obj.messages.filter(role='assistant').count()} | Admin: {obj.messages.filter(role='human_agent').count()}"

    @display
    def credit_used(self, obj):
        if obj.message_credit_used or obj.tool_credit_used:
            return f"Reply: {obj.message_credit_used} | Tool Call: {obj.tool_credit_used}"
        return "-"
    
    def has_add_permission(self, request):
        return False
    


