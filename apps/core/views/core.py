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

def info_view(request, endpoint):
    page = get_object_or_404(InfoPage, slug=endpoint)
    context = {
        'title': page.title,
        'description': page.description,
        'content': page.content,
    }
    return render(request, 'core/info_page.html', context)