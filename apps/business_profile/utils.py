from django.conf import settings

def order_api_schema(order):
    profile_pic_url = None
    if order.customer and order.customer.profile_pic:
        profile_pic_url = f"{settings.SITE_URL}{order.customer.profile_pic.url}"
    return {
        'id': order.id,
        'customer': {
            'id': order.customer.id if order.customer else None,
            'name': order.customer.name if order.customer else None,
            'platform': order.customer.business_profile.platform_name if order.customer else None,
            'platform_id': order.customer.platform_id if order.customer else None,
            'profile_pic': profile_pic_url,
        },
        'conversation_id': order.conversation.id if order.conversation else None,
        'fields': order.fields,
        'created_at': order.created_at.isoformat(),
        'updated_at': order.updated_at.isoformat(),
    }

