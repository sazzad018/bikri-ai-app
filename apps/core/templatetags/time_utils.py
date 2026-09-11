from django import template
from django.utils import timezone
from django.utils.translation import gettext as _

register = template.Library()

@register.filter
def short_timesince(value):
    if not value:
        return ""

    now = timezone.now()
    diff = now - value

    seconds = int(diff.total_seconds())
    
    if seconds < 0:
        return _("0s")

    # Define thresholds in seconds
    intervals = (
        ('y', 31536000),  # 60 * 60 * 24 * 365
        ('mo', 2592000), # 60 * 60 * 24 * 30
        ('w', 604800),   # 60 * 60 * 24 * 7
        ('d', 86400),    # 60 * 60 * 24
        ('h', 3600),     # 60 * 60
        ('m', 60),
        ('s', 1),
    )

    for unit, count in intervals:
        time = seconds // count
        if time >= 1:
            return f"{time}{unit}"

    return _("0s")