import requests, secrets, logging
from django.conf import settings
from django.shortcuts import redirect
from django.core.files.base import ContentFile
from django.urls import reverse
from django.views import View
from urllib.parse import urlencode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.accounts.models import User
from apps.business_profile.models import BusinessProfile

logger = logging.getLogger(__name__)

FACEBOOK_GRAPH_API_URL = settings.FACEBOOK_GRAPH_API_URL

@login_required
def facebook_oauth_init(request):
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    params = {
        "client_id": settings.FACEBOOK_APP_ID,
        "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
        "scope": ",".join([
            "pages_show_list",
            "pages_messaging",
            "business_management",
            "pages_manage_metadata",
            "pages_read_engagement",
            "pages_read_user_content",
            "pages_manage_engagement",
        ]),
        "response_type": "code",
        "state": state,
    }
    url = "https://www.facebook.com/dialog/oauth?" + urlencode(params)
    return redirect(url)



class FacebookOAuthCallbackView(LoginRequiredMixin, View):
    def get(self, request):
        code = request.GET.get("code")
        error = request.GET.get("error")
        state = request.GET.get("state")
        
        redirect_url = reverse("admin:business_profile_businessprofile_changelist")
        
        if error:
            messages.error(request, error)
            logger.error(f"Facebook OAuth Error: {error}")
            return redirect(redirect_url)

        if state != request.session.pop("oauth_state", None):
            messages.error(request, "OAuth state mismatch.")
            logger.error("OAuth state mismatch.")
            return redirect(redirect_url)

        user = request.user

        # Exchange code for a short-lived user access token
        token_resp = requests.get(f"{FACEBOOK_GRAPH_API_URL}/oauth/access_token", params={
            "client_id": settings.FACEBOOK_APP_ID,
            "client_secret": settings.FACEBOOK_APP_SECRET,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "code": code,
        })
        token_data = token_resp.json()
        short_lived_user_token = token_data.get("access_token")

        if not short_lived_user_token:
            err = "Failed to obtain access token from Facebook."
            messages.error(request, err)
            logger.error(err)
            return redirect(redirect_url)

        # Exchange for a long-lived user access token
        long_lived_resp = requests.get(f"{FACEBOOK_GRAPH_API_URL}/oauth/access_token", params={
            "grant_type": "fb_exchange_token",
            "client_id": settings.FACEBOOK_APP_ID,
            "client_secret": settings.FACEBOOK_APP_SECRET,
            "fb_exchange_token": short_lived_user_token,
        })
        long_lived_token = long_lived_resp.json().get("access_token")
        if not long_lived_token:
            err = "Failed to exchange for long-lived token."
            messages.error(request, err)
            logger.error(err)
            return redirect(redirect_url)

        # Fetch pages the user manages
        pages_resp = requests.get(f"{FACEBOOK_GRAPH_API_URL}/me/accounts", params={
            "access_token": long_lived_token,
            "fields": "id,name,access_token,picture"
        })
        pages = pages_resp.json().get("data", [])

        if not pages:
            err = "Failed to retrieve pages. It may be due to insufficient permissions."
            messages.error(request, err)
            logger.error(err)
            return redirect(redirect_url)

        #list pages id
        # Check if any of the pages are already connected to other accounts, ignore them
        page_ids = [page["id"] for page in pages]
        business_profiles = BusinessProfile.objects.filter(platform_id__in=page_ids, platform_name='facebook').exclude(user=user)
        final_pages = []
        ignored_pages = []
        for page in pages:
            page_id = page["id"]
            if business_profiles.filter(platform_id=page_id).exists():
                ignored_pages.append(page)
            else:
                final_pages.append(page)

        ignored_page_names = [page["name"] for page in ignored_pages]
        if ignored_page_names:
            err = f"{', '.join(ignored_page_names)} already connected to other accounts."
            messages.warning(request, err)
            logger.warning(err)
            
        results = []
        for page in final_pages:
            page_id = page["id"]
            page_name = page["name"]
            page_access_token = page["access_token"]
            try:
                page_profile_pic = requests.get(page["picture"]["data"]["url"]).content
                profile, created = BusinessProfile.objects.update_or_create(
                    platform_id=page_id,
                    user=user,
                    platform_name='facebook',
                    defaults={"name": page_name, "platform_access_token": page_access_token}
                )
                if created or not profile.profile_pic:
                    page_profile_pic = requests.get(page["picture"]["data"]["url"]).content
                    profile.profile_pic.save(f'facebook_page_{page_id}.jpg', ContentFile(page_profile_pic))
            except Exception as e:
                err = f"Failed to update or create business profile for page: {page_name}"
                logger.exception(err)
                messages.error(request, err)
                continue

            # Subscribe the page to the Messenger webhook
            subscribe_result = subscribe_page_to_webhook(page_id, page_access_token)
            results.append({
                "page_id": page_id,
                "page_name": page_name,
                "webhook_subscribed": subscribe_result,
            })
            
        if results:
            page_names = [result["page_name"] for result in results]
            messages.success(request, "Successfully connected to Facebook pages: " + ", ".join(page_names))
            failed_webhook_pages = [result["page_name"] for result in results if not result["webhook_subscribed"]]
            if failed_webhook_pages:
                err = "Failed to subscribe to webhook for pages: " + ", ".join(failed_webhook_pages)
                messages.warning(request, err)
                logger.warning(err)
        else:
            messages.error(request, "Failed to connect any Facebook pages.")
            logger.error("Failed to connect any Facebook pages.")

        return redirect(redirect_url)

#helper function, not view
def subscribe_page_to_webhook(page_id: str, page_access_token: str) -> bool:
    resp = requests.post(
        f"{FACEBOOK_GRAPH_API_URL}/{page_id}/subscribed_apps",
        params={
            "access_token": page_access_token,
            "subscribed_fields": "messages,messaging_postbacks,message_echoes,feed",
        }
    )
    data = resp.json()
    if not data.get("success", False):
        logger.error(f"Webhook subscription failed for page {page_id}: {data}")
    return data.get("success", False)

