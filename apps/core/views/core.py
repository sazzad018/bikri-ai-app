import os
import re
import html
from pathlib import Path
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from apps.core.models import InfoPage, HomePage, SiteConfig
from apps.credit.models import CreditPackage


def landing(request):
    site_config = SiteConfig.get_solo()
    context = {
        "site": HomePage.objects.first(),
        "packages": CreditPackage.objects.filter(is_active=True),
        "credit_per_reply": site_config.credit_per_reply,
        "credit_per_comment": site_config.credit_per_comment,
    }
    return render(request, 'core/landing.html', context)


def markdown_to_html(text):
    try:
        import markdown
        return markdown.markdown(text, extensions=['extra', 'tables', 'fenced_code'])
    except Exception:
        lines = text.split('\n')
        html_lines = []
        in_list = False
        for line in lines:
            sline = line.strip()
            if not sline:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                continue
            if sline.startswith('# '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h1>{html.escape(sline[2:])}</h1>')
            elif sline.startswith('## '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h2>{html.escape(sline[3:])}</h2>')
            elif sline.startswith('### '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h3>{html.escape(sline[4:])}</h3>')
            elif sline.startswith('- '):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                html_lines.append(f'<li>{html.escape(sline[2:])}</li>')
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<p>{html.escape(sline)}</p>')
        if in_list:
            html_lines.append('</ul>')
        return '\n'.join(html_lines)


def get_markdown_page(endpoint):
    info_dir = Path(settings.BASE_DIR) / 'templates' / 'core' / 'info'
    file_path = info_dir / f"{endpoint}.md"
    if not file_path.exists():
        alt_name = endpoint.replace('_', '-')
        file_path = info_dir / f"{alt_name}.md"

    if not file_path.exists():
        return None

    raw_content = file_path.read_text(encoding='utf-8')

    defaults = {
        '{last_updated_date}': 'January 1, 2026',
        '{platform_name}': 'Cholbe AI',
        '{support_email}': os.environ.get('MAIN_EMAIL_HOST_USER', 'support@cholbe.ai') or 'support@cholbe.ai',
        '{conversation_retention_days}': '90',
        '{security_measure_1}': 'End-to-end encryption for API communications (HTTPS/TLS)',
        '{security_measure_2}': 'Encrypted database storage and secure credential management',
        '{security_measure_3}': 'Strict access controls and regular security auditing',
        '{minimum_age}': '18',
        '{street_address}': 'Dhaka',
        '{city}': 'Dhaka',
        '{postal_code}': '1200',
        '{country}': 'Bangladesh',
        '{governing_country}': 'Bangladesh',
        '{jurisdiction_city}': 'Dhaka',
        '{currency}': 'BDT',
        '{credit_per_conversation}': '1',
        '{expire / do not expire}': 'do not expire',
        '{credit_expiration_details}': 'Credits remain valid as long as your account is active.',
        '{rate_limit}': 'standard API rate limits',
        '{uptime_percentage}': '99.5',
        '{maintenance_notice_hours}': '24',
        '{liability_period_months}': '12',
        '{full_refund_hours}': '24',
        '{partial_refund_days}': '7',
        '{purchase_amount}': 'Total amount',
        '{used_credits}': 'Used credits',
        '{credit_unit_price}': 'Unit price',
        '{outage_threshold_hours}': '24',
        '{refund_deadline_days}': '14',
        '{verification_days}': '3',
        '{processing_days}': '5',
        '{address}': 'Dhaka, Bangladesh',
        '{phone_number}': '+880 1700-000000',
        '{phone_availability_hours}': '10:00 AM - 6:00 PM',
        '{phone_availability_days}': 'Sunday to Thursday',
        '{facebook_page_url}': 'https://facebook.com',
        '{whatsapp_number}': '+880 1700-000000',
        '{whatsapp_number_intl}': '880170000000',
        '{day_1}': 'Sunday',
        '{hours_1}': '9:00 AM - 6:00 PM',
        '{day_2}': 'Monday',
        '{hours_2}': '9:00 AM - 6:00 PM',
        '{day_3}': 'Tuesday',
        '{hours_3}': '9:00 AM - 6:00 PM',
        '{day_4}': 'Wednesday',
        '{hours_4}': '9:00 AM - 6:00 PM',
        '{day_5}': 'Thursday',
        '{hours_5}': '9:00 AM - 6:00 PM',
        '{saturday_hours}': '10:00 AM - 4:00 PM',
        '{sunday_hours}': 'Closed',
    }

    for key, val in defaults.items():
        raw_content = raw_content.replace(key, str(val))

    raw_content = re.sub(r'\{[a-zA-Z0-9_/ -]+\}', '', raw_content)

    title = endpoint.replace('-', ' ').replace('_', ' ').title()
    for line in raw_content.splitlines():
        if line.startswith('# '):
            title = line[2:].strip()
            break

    html_content = markdown_to_html(raw_content)

    return {
        'title': title,
        'description': f"{title} - Cholbe AI",
        'content': html_content,
    }


def info_view(request, endpoint):
    page = InfoPage.objects.filter(slug=endpoint).first()
    if page:
        context = {
            'title': page.title,
            'description': page.description,
            'content': page.content,
        }
    else:
        md_data = get_markdown_page(endpoint)
        if md_data:
            context = md_data
            # Try to persist into DB so it can be edited from admin later
            try:
                InfoPage.objects.get_or_create(
                    slug=endpoint,
                    defaults={
                        'title': md_data['title'],
                        'description': md_data['description'],
                        'content': md_data['content'],
                    }
                )
            except Exception:
                pass
        else:
            page = get_object_or_404(InfoPage, slug=endpoint)
            context = {
                'title': page.title,
                'description': page.description,
                'content': page.content,
            }

    return render(request, 'core/info_page.html', context)