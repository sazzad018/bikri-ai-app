import json
import logging
import secrets

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from apps.business_profile.models import BusinessProfile

logger = logging.getLogger(__name__)

FACEBOOK_GRAPH_API_URL = settings.FACEBOOK_GRAPH_API_URL

COEXISTENCE_FINISH_EVENTS = frozenset({
    "FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING",
})
SUCCESS_FINISH_EVENTS = COEXISTENCE_FINISH_EVENTS | frozenset({
    "FINISH",
    "FINISH_ONLY_WABA",
    "FINISH_OBO_MIGRATION",
    "FINISH_GRANT_ONLY_API_ACCESS",
})


def _graph_get(path, *, params=None, token=None, timeout=10):
    params = dict(params or {})
    if token:
        params["access_token"] = token
    return requests.get(f"{FACEBOOK_GRAPH_API_URL}/{path}", params=params, timeout=timeout)


def _graph_post(path, *, json_body=None, token=None, timeout=10):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.post(
        f"{FACEBOOK_GRAPH_API_URL}/{path}",
        headers=headers,
        json=json_body,
        timeout=timeout,
    )


def exchange_embedded_signup_code(code: str) -> str | None:
    """Exchange Embedded Signup code for a business integration token (no redirect_uri)."""
    try:
        resp = _graph_get("oauth/access_token", params={
            "client_id": settings.FACEBOOK_APP_ID,
            "client_secret": settings.FACEBOOK_APP_SECRET,
            "code": code,
        })
        data = resp.json()
    except requests.RequestException:
        logger.exception("Failed to reach Meta while exchanging Embedded Signup code.")
        return None

    if "error" in data:
        logger.error("Embedded Signup token exchange error: %s", data["error"])
        return None
    return data.get("access_token")


def subscribe_waba_webhooks(waba_id: str, business_token: str) -> bool:
    try:
        resp = _graph_post(f"{waba_id}/subscribed_apps", token=business_token)
        return resp.json().get("success", False)
    except requests.RequestException:
        logger.exception("Failed to subscribe WABA %s to webhooks.", waba_id)
        return False


def fetch_phone_number_details(phone_number_id: str, business_token: str) -> dict:
    try:
        resp = _graph_get(
            phone_number_id,
            params={"fields": "display_phone_number,verified_name,is_on_biz_app,platform_type"},
            token=business_token,
        )
        return resp.json()
    except requests.RequestException:
        logger.exception("Failed to fetch phone number details for %s.", phone_number_id)
        return {}


def save_whatsapp_business_profile(
    *,
    user,
    phone_number_id: str,
    waba_id: str,
    business_token: str,
    display_name: str,
) -> bool:
    existing = BusinessProfile.objects.filter(
        platform_id=phone_number_id,
        platform_name="whatsapp",
    ).exclude(user=user).exists()
    if existing:
        logger.warning("WhatsApp number %s already connected to another account.", display_name)
        return False

    BusinessProfile.objects.update_or_create(
        platform_id=phone_number_id,
        platform_name="whatsapp",
        defaults={
            "user": user,
            "name": display_name,
            "waba_id": waba_id,
            "platform_access_token": business_token,
        },
    )
    return True


@login_required
def whatsapp_oauth_init(request):
    state = secrets.token_urlsafe(32)
    request.session["whatsapp_oauth_state"] = state
    return render(request, "business_profile/whatsapp_embedded_signup.html", {
        "facebook_app_id": settings.FACEBOOK_APP_ID,
        "config_id": settings.WHATSAPP_EMBEDDED_SIGNUP_CONFIG_ID,
        "graph_api_version": settings.FACEBOOK_GRAPH_API_VERSION,
        "callback_url": request.build_absolute_uri(
            reverse("business_profile:whatsapp_oauth_callback")
        ),
        "state": state,
        "redirect_url": reverse("admin:business_profile_businessprofile_changelist"),
    })


@method_decorator(csrf_exempt, name="dispatch")
class WhatsAppOAuthCallbackView(LoginRequiredMixin, View):
    """Handle Embedded Signup v4 callback with coexistence support."""

    def post(self, request):
        redirect_url = reverse("admin:business_profile_businessprofile_changelist")

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)

        code = payload.get("code")
        session_data = payload.get("session_data") or {}
        state = payload.get("state")

        if state != request.session.pop("whatsapp_oauth_state", None):
            logger.error("WhatsApp Embedded Signup state mismatch.")
            return JsonResponse({"error": "OAuth state mismatch."}, status=400)

        finish_event = session_data.get("event")
        phone_number_id = session_data.get("phone_number_id")
        waba_id = session_data.get("waba_id")

        if finish_event == "CANCEL":
            error_message = (session_data.get("data") or {}).get("error_message")
            if error_message:
                messages.warning(request, f"WhatsApp signup cancelled: {error_message}")
            else:
                messages.warning(request, "WhatsApp signup was cancelled.")
            return JsonResponse({"redirect_url": redirect_url})

        if finish_event not in SUCCESS_FINISH_EVENTS:
            messages.error(request, "WhatsApp signup did not complete successfully.")
            logger.error("Unexpected Embedded Signup event: %s", finish_event)
            return JsonResponse({"error": "Signup did not complete."}, status=400)

        if not code:
            messages.error(request, "Missing authorization code from Meta.")
            return JsonResponse({"error": "Missing authorization code."}, status=400)

        if not phone_number_id or not waba_id:
            messages.error(request, "Missing WhatsApp asset IDs from signup session.")
            return JsonResponse({"error": "Missing asset IDs."}, status=400)

        business_token = exchange_embedded_signup_code(code)
        if not business_token:
            messages.error(request, "Failed to obtain access token from Meta.")
            return JsonResponse({"error": "Token exchange failed."}, status=502)

        if not subscribe_waba_webhooks(waba_id, business_token):
            messages.warning(
                request,
                "Connected but failed to subscribe to WhatsApp webhooks. "
                "Message delivery may not work until this is resolved.",
            )

        phone_details = fetch_phone_number_details(phone_number_id, business_token)
        display_name = (
            phone_details.get("display_phone_number")
            or phone_details.get("verified_name")
            or phone_number_id
        )

        saved = save_whatsapp_business_profile(
            user=request.user,
            phone_number_id=phone_number_id,
            waba_id=waba_id,
            business_token=business_token,
            display_name=display_name,
        )
        if not saved:
            messages.error(
                request,
                f"{display_name} is already connected to another account.",
            )
            return JsonResponse({"error": "Number already connected."}, status=409)


        messages.success(request, f"Successfully connected {display_name}.")
        return JsonResponse({"redirect_url": redirect_url})

    def get(self, request):
        """Legacy OAuth redirect callback — redirect users to the new flow."""
        messages.info(
            request,
            "WhatsApp now uses Embedded Signup. Please connect again using the WhatsApp button.",
        )
        return redirect(reverse("admin:business_profile_businessprofile_changelist"))
