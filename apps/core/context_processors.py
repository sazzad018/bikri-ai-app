from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

def google_tag_manager(request):
    if not hasattr(request, '_gtm_events'):
        request._gtm_events = []

        is_ajax = (
            request.headers.get('HX-Request') == 'true' or
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        )

        if not is_ajax:
            allowed_session_events = (
                ('gtm_signup', 'gtm.user_signup'),
                ('gtm_payment_success', 'gtm.payment_success'),
                ('gtm_logout', 'gtm.user_logout')
            )
            for session_key, event_name in allowed_session_events:
                if hasattr(request, 'session') and session_key in request.session:
                    event_data = request.session.pop(session_key)
                    request._gtm_events.append(json.dumps({
                        'event': event_name,
                        **event_data,
                    }))

    logger.debug(request._gtm_events)

    return {
        'GOOGLE_TAG_MANAGER_ID': settings.GOOGLE_TAG_MANAGER_ID,
        'gtm_events': request._gtm_events,
    }
