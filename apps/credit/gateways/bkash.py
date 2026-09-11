from . import BasePaymentAdapter
import requests
from django.conf import settings
import os

class BkashAdapter(BasePaymentAdapter):
    method_key = 'bkash'
    is_redirect = True

    def __init__(self):
        self.app_key = os.environ.get('BKASH_APP_KEY', '')
        self.app_secret = os.environ.get('BKASH_APP_SECRET', '')
        self.username = os.environ.get('BKASH_USERNAME', '')
        self.password = os.environ.get('BKASH_PASSWORD', '')
        self.base_url = os.environ.get('BKASH_BASE_URL', 'https://tokenized.sandbox.bka.sh/v1.2.0-beta').rstrip('/')
    
    def _build_url(self, endpoint):
        # Allow user to specify direct base_url. If they provide tokenized.sandbox.bka.sh/v1.2.0-beta,
        # we append /tokenized/checkout manually if it's not present.
        if '/tokenized/checkout' not in self.base_url and '/checkout/tokenized' not in self.base_url:
            return f"{self.base_url}/tokenized/checkout/{endpoint}"
        return f"{self.base_url}/{endpoint}"

    def grant_token(self):
        url = self._build_url('token/grant')
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "username": self.username,
            "password": self.password,
        }
        payload = {
            "app_key": self.app_key,
            "app_secret": self.app_secret
        }
        res = requests.post(url, json=payload, headers=headers)
        res.raise_for_status()
        return res.json().get('id_token')
        
    def create_payment(self, amount, reference, callback_url):
        id_token = self.grant_token()
        
        url = self._build_url('create')
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": id_token,
            "X-APP-Key": self.app_key
        }
        payload = {
            "mode": "0011",
            "payerReference": " ",
            "callbackURL": callback_url,
            "amount": str(amount),
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": reference
        }
        res = requests.post(url, json=payload, headers=headers)
        res.raise_for_status()
        data = res.json()
        
        # bkashURL is for the frontend to redirect
        return {
            "paymentID": data.get("paymentID"),
            "redirectURL": data.get("bkashURL")
        }

    def execute_payment(self, payment_id):
        id_token = self.grant_token()
        
        url = self._build_url('execute')
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": id_token,
            "X-APP-Key": self.app_key
        }
        payload = {
            "paymentID": payment_id
        }
        res = requests.post(url, json=payload, headers=headers)
        res.raise_for_status()
        return res.json()

