from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.business_profile.models import Order
from apps.core.utils import run_in_thread
from apps.business_profile.utils import order_api_schema
import requests
import hmac
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

def send_webhook_request(business_profile, order, created):
    url = business_profile.webhook_url
    if not url:
        return
    
    if not business_profile.api_key:
        logger.warning(f"Webhook enabled for BusinessProfile {business_profile.id} but no API key exists. Skipping webhook.")
        return
    
    payload = order_api_schema(order)
    payload_json = json.dumps(payload)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Cholbe-AI-Webhook/1.0"
    }
    
    signature = hmac.new(
        business_profile.api_key.encode('utf-8'),
        payload_json.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    headers["X-SAE-Signature"] = signature
    headers["X-Signature"] = signature

    try:
        response = requests.post(url, data=payload_json, headers=headers, timeout=10)
        logger.info(f"Webhook delivered for Order {order.id} to {url}. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to deliver webhook for Order {order.id} to {url}: {str(e)}")


@receiver(post_save, sender=Order)
def trigger_order_webhook_signal(sender, instance, created, **kwargs):
    business_profile = instance.business_profile
    if business_profile.webhook_enabled and business_profile.webhook_url:
        run_in_thread(send_webhook_request, business_profile, instance, created)
