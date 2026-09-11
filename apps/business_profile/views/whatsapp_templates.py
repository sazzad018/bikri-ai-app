import re
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from apps.business_profile.models import WhatsappTemplate

@login_required
def load_template_variables(request):
    template_id = request.GET.get('template_id')
    template = get_object_or_404(WhatsappTemplate, id=template_id, business_profile__user=request.user)
    
    # Extract placeholders from the BODY component text
    body_text = ""
    for comp in template.components or []:
        if comp.get('type') == 'BODY':
            body_text = comp.get('text', '')
            break

    # Find all {{1}}, {{2}}... variables
    placeholder_pattern = re.compile(r'\{\{(\d+)\}\}')
    matches = placeholder_pattern.findall(body_text)
    
    # Unique sorted integer variables
    variables = sorted(list(set(int(m) for m in matches)))

    if not variables:
        return HttpResponse("""
            <div class="p-4 rounded-lg bg-neutral-50 border border-neutral-200 dark:bg-neutral-800/50 dark:border-neutral-700">
                <p class="text-sm font-medium text-neutral-600 dark:text-neutral-400">
                    This template does not require any variables. It is ready to send.
                </p>
            </div>
        """)

    # Render inputs for variables
    # We will build HTML directly to keep it simple and ultra-responsive
    html_parts = [
        '<div class="flex flex-col gap-4">'
        '<div class="flex items-center gap-2 mb-1">'
        '  <span class="material-symbols-outlined text-neutral-400 text-lg">tune</span>'
        '  <h3 class="text-sm font-semibold text-neutral-700 dark:text-neutral-300">Template Variables</h3>'
        '</div>'
    ]

    for var_num in variables:
        html_parts.append(f"""
        <div class="flex flex-col gap-2 p-4 border border-neutral-200 rounded-lg bg-neutral-50/50 dark:border-neutral-700 dark:bg-neutral-800/30">
            <div class="flex items-center justify-between gap-4">
                <label class="text-sm font-semibold text-neutral-700 dark:text-neutral-300">
                    Variable {{{{{var_num}}}}}
                </label>
                <select name="var_{var_num}_type" 
                        class="text-xs border border-neutral-300 rounded px-2.5 py-1 bg-white text-neutral-700 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-300 focus:outline-none focus:ring-1 focus:ring-primary-500"
                        onchange="const inputDiv = this.closest('div').nextElementSibling; if (this.value !== 'custom') {{ inputDiv.classList.add('hidden'); }} else {{ inputDiv.classList.remove('hidden'); }}">
                    <option value="custom">Custom Text</option>
                    <option value="customer_name">Customer Name</option>
                    <option value="customer_phone">Customer Phone (ID)</option>
                    <option value="business_name">Business Name</option>
                    <option value="current_date">Current Date</option>
                    <option value="current_time">Current Time</option>
                </select>
            </div>
            <div class="mt-1">
                <input type="text" name="var_{var_num}_value" placeholder="Enter custom value for {{{{{var_num}}}}}"
                       class="w-full text-sm border border-neutral-300 rounded px-3 py-2 bg-white text-neutral-800 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100 focus:outline-none focus:ring-1 focus:ring-primary-500" />
            </div>
        </div>
        """)

    html_parts.append('</div>')
    return HttpResponse("".join(html_parts))
