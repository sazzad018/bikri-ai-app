import json
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from apps.business_profile.models import BusinessProfile, Order
from apps.business_profile.utils import order_api_schema

def api_key_auth(view_func):
    """
    Decorator for API authentication using X-API-Key.
    """
    def _wrapped_view(request, *args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return JsonResponse({'error': 'Missing X-API-Key header.'}, status=401)
        
        business_profile = BusinessProfile.objects.filter(api_key=api_key, api_enabled=True).first()
        if not business_profile:
            return JsonResponse({'error': 'Invalid API key, or API access is disabled.'}, status=403)
        
        request.business_profile = business_profile
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@method_decorator(csrf_exempt, name='dispatch')
class OrderAPIView(View):
    @method_decorator(api_key_auth)
    def get(self, request):
        """
        List all orders for the authenticated business profile with optional filtering.
        Supported query filters:
        - created_at__gte: filter by creation date/time greater than or equal to (ISO format)
        - created_at__lte: filter by creation date/time less than or equal to (ISO format)
        - q: search for substring in the order's fields
        """
        queryset = Order.objects.filter(business_profile=request.business_profile).select_related('customer', 'conversation')

        created_at_gte = request.GET.get('created_at__gte')
        if created_at_gte:
            try:
                queryset = queryset.filter(created_at__gte=created_at_gte)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Invalid created_at__gte format. Use ISO format (e.g. YYYY-MM-DD).'}, status=400)
                
        created_at_lte = request.GET.get('created_at__lte')
        if created_at_lte:
            try:
                queryset = queryset.filter(created_at__lte=created_at_lte)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Invalid created_at__lte format. Use ISO format (e.g. YYYY-MM-DD).'}, status=400)
                
        q = request.GET.get('q')

        # Ordering
        queryset = queryset.order_by('-created_at')

        data = []
        for order in queryset:
            if q:
                # Safe case-insensitive substring search in JSON fields values
                fields_dict = order.fields or {}
                if not any(q.lower() in str(val).lower() for val in fields_dict.values()):
                    continue
            data.append(order_api_schema(order))
            
        return JsonResponse(data, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class OrderAPIDetailView(View):
    @method_decorator(api_key_auth)
    def get(self, request, order_id):
        """
        Retrieve details of a single order.
        """
        order = Order.objects.filter(id=order_id, business_profile=request.business_profile).select_related('customer', 'conversation').first()
        if not order:
            return JsonResponse({'error': f'Order with ID {order_id} not found.'}, status=404)

        return JsonResponse(order_api_schema(order), safe=False)
