from django.utils import timezone


def build_payment_gtm_event(attempt):
    """
    Build the GTM event dict for a successful payment attempt.
    Returns a plain dict (not JSON-serialized).
    """
    return {
        'id': str(attempt.id),
        'user_id': attempt.user.id,
        'amount': attempt.amount,
        'package_id': attempt.package.id if attempt.package else None,
        'package_title': attempt.package.title if attempt.package else 'Custom Package',
        'credits': attempt.package.credits if attempt.package else 0,
        'payment_method': attempt.payment_method,
        'manual_transaction_id': attempt.manual_transaction_id,
        'currency': 'BDT',
        'timestamp': attempt.verified_at.timestamp() if attempt.verified_at else timezone.now().timestamp(),
    }