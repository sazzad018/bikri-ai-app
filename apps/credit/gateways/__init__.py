from django.conf import settings
from django.utils.module_loading import import_string


class BasePaymentAdapter:
    """
    Base class for all payment adapters.
    """
    method_key: str = ''
    is_redirect: bool = True

    def create_payment(self, amount, reference, callback_url):
        raise NotImplementedError

    def execute_payment(self, payment_id):
        raise NotImplementedError


ADAPTERS = {
    'bkash': 'apps.credit.gateways.bkash.BkashAdapter',
    'manual':     'apps.credit.gateways.manual.ManualPaymentAdapter',
}


def get_payment_adapter() -> BasePaymentAdapter:
    """
    Returns an instance of the payment adapter configured in
    settings.PAYMENT_ADAPTER (default: 'manual').
    """
    key = getattr(settings, 'PAYMENT_ADAPTER', 'manual')
    dotted_path = ADAPTERS.get(key)
    if not dotted_path:
        raise ValueError(f"Unknown PAYMENT_ADAPTER '{key}'. Choices: {list(ADAPTERS.keys())}")
    cls = import_string(dotted_path)
    return cls()
