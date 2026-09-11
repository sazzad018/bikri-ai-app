import json
from datetime import timedelta

from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate, ExtractHour, TruncHour

from apps.business_profile.models import Message, Conversation, Order
from apps.core.forms import AnalyticsFilterForm


TIME_RANGE_DAYS = {
    '1d': 1,
    '3d': 3,
    '7d': 7,
    '30d': 30,
    '90d': 90,
    '180d': 180,
    '365d': 365,
}

def dashboard_callback(request, context):
    business_profiles = list(request.user.business_profiles.all())
    first_profile = business_profiles[0] if business_profiles else None

    # Handle users with no business profiles
    if not first_profile:
        context.update({
            "title": "Dashboard",
            "incoming_messages": 0, "outgoing_messages": 0,
            "conversations_count": 0, "orders_count": 0,
            "chart_day_labels": "[]", "chart_incoming": "[]",
            "chart_outgoing": "[]", "chart_conversations": "[]",
            "chart_orders": "[]", "chart_hour_labels": "[]",
            "chart_engagement": "[]",
            "popup": request.user.get_popup(),
        })
        return context

    # Safely populate form defaults
    data = request.GET.copy()
    data.setdefault('business_profile', first_profile.id)
    data.setdefault('time_range', '7d')

    form = AnalyticsFilterForm(data)
    form.fields['business_profile'].choices = [(bp.id, bp.name) for bp in business_profiles]

    if form.is_valid():
        selected_profile_id = form.cleaned_data['business_profile']
        time_range_key = form.cleaned_data['time_range']
    else:
        selected_profile_id = first_profile.id
        time_range_key = '7d'

    days = TIME_RANGE_DAYS.get(time_range_key, 1)
    since = timezone.now() - timedelta(days=days)

    # Streamlined Querysets 
    messages_qs = Message.global_objects.filter(
        conversation__business_profile_id=selected_profile_id, 
        created_at__gte=since
    )
    conversations_qs = Conversation.global_objects.filter(
        business_profile_id=selected_profile_id, 
        created_at__gte=since
    )
    orders_qs = Order.global_objects.filter(
        business_profile_id=selected_profile_id, 
        created_at__gte=since
    )

    # --- Stat cards ---
    incoming_messages = messages_qs.filter(role='user').count()
    outgoing_messages = messages_qs.filter(role__in=['assistant', 'human_agent']).count()
    conversations_count = conversations_qs.count()
    orders_count = orders_qs.count()

    # --- Bar Chart Aggregation ---
    
    # 1. Generate periods (24 hours for 1d, otherwise daily dates)
    if days == 1:
        now = timezone.localtime(timezone.now()).replace(minute=0, second=0, microsecond=0)
        all_periods = [now - timedelta(hours=i-2) for i in range(23, -1, -1)]
        target_length = 8
        total_points = 24
    else:
        today = timezone.now().date()
        all_periods = [today - timedelta(days=i) for i in range(days-1, -1, -1)]
        total_points = days
        
        if days <= 7:
            target_length = days
        elif days <= 30:
            target_length = 5
        elif days <= 90:
            target_length = 10
        else:
            target_length = 12
            
        target_length = min(days, target_length)

    # 2. Fetch aggregations from DB (using TruncHour or TruncDate)
    trunc_func = TruncHour('created_at') if days == 1 else TruncDate('created_at')
    
    def get_time_counts(queryset):
        counts = queryset.annotate(period=trunc_func).values('period').annotate(count=Count('id'))
        # FIX 1: Normalize DB datetime output to ISO strings so we don't have naive vs tz-aware dict key misses
        return {item['period'].isoformat(): item['count'] for item in counts if item['period']}

    # Single query optimization for messages
    msg_counts = messages_qs.annotate(period=trunc_func).values('period', 'role').annotate(count=Count('id'))
    incoming_by_period, outgoing_by_period = {}, {}
    for item in msg_counts:
        if not item['period']: continue
        p_key = item['period'].isoformat()
        if item['role'] == 'user':
            incoming_by_period[p_key] = incoming_by_period.get(p_key, 0) + item['count']
        elif item['role'] in ['assistant', 'human_agent']:
            outgoing_by_period[p_key] = outgoing_by_period.get(p_key, 0) + item['count']

    conv_by_period = get_time_counts(conversations_qs)
    orders_by_period = get_time_counts(orders_qs)

    # 3. Build full unsampled arrays (using the same ISO normalization)
    incoming_full = [incoming_by_period.get(p.isoformat(), 0) for p in all_periods]
    outgoing_full = [outgoing_by_period.get(p.isoformat(), 0) for p in all_periods]
    conv_full     = [conv_by_period.get(p.isoformat(), 0) for p in all_periods]
    orders_full   = [orders_by_period.get(p.isoformat(), 0) for p in all_periods]

    # FIX 4: Use max() to prevent ZeroDivisionError/ValueError if length logic fails in weird states
    chunk_size = max(1, total_points // target_length) if target_length > 0 else 1

    # 4. Downsample
    def resize_list(data):
        res = [sum(data[i : i + chunk_size]) for i in range(0, len(data), chunk_size)]
        # FIX 2: Force it to never exceed the target_length by slicing
        return res[:target_length]

    incoming_series = resize_list(incoming_full)
    outgoing_series = resize_list(outgoing_full)
    conv_series     = resize_list(conv_full)
    orders_series   = resize_list(orders_full)

    # 5. Generate X-axis labels exactly mapped to the downsampling logic
    day_labels =[]
    for i in range(0, total_points, chunk_size):
        chunk_start = all_periods[i]
        if days == 1:
            day_labels.append(chunk_start.strftime('%I %p'))
        elif days <= 7:
            day_labels.append(chunk_start.strftime('%a'))
        elif days <= 90:
            day_labels.append(chunk_start.strftime('%b %d'))
        else:
            day_labels.append(chunk_start.strftime('%b %Y'))
            
    # FIX 3: Slice labels tightly so labels array perfectly matches series array length
    day_labels = day_labels[:target_length]

    # --- Hourly engagement chart ---
    hour_buckets = [i for i in range(0, 24, 3)]
    hour_labels = [f"{(i % 12 or 12)} {'AM' if i < 12 else 'PM'}" for i in range(0, 24, 3)]

    hourly_counts = dict(
        messages_qs.filter(role='user')
        .annotate(hour=ExtractHour('created_at'))
        .values('hour')
        .annotate(count=Count('id'))
        .values_list('hour', 'count')
    )

    engagement_series =[]
    for bucket_start in hour_buckets:
        count = hourly_counts.get(bucket_start, 0) + hourly_counts.get((bucket_start + 1) % 24, 0)
        engagement_series.append(count)

    total_engagement = sum(engagement_series) or 1
    engagement_pct = [round(v / total_engagement * 100, 1) for v in engagement_series]

    # --- Context Update ---
    context.update({
        "title": "Dashboard",
        "form": form,
        # Stat cards
        "incoming_messages": incoming_messages,
        "outgoing_messages": outgoing_messages,
        "conversations_count": conversations_count,
        "orders_count": orders_count,
        # Weekly/Monthly chart
        "chart_day_labels": json.dumps(day_labels),
        "chart_incoming": json.dumps(incoming_series),
        "chart_outgoing": json.dumps(outgoing_series),
        "chart_conversations": json.dumps(conv_series),
        "chart_orders": json.dumps(orders_series),
        # Engagement chart
        "chart_hour_labels": json.dumps(hour_labels),
        "chart_engagement": json.dumps(engagement_pct),

        "popup": request.user.get_popup(),
    })
    return context