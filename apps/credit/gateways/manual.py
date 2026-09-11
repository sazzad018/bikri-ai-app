from . import BasePaymentAdapter
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
import logging
import os

logger = logging.getLogger(__name__)

# The bKash number users should send money to


class ManualPaymentAdapter(BasePaymentAdapter):
    """
    Manual payment adapter: instead of redirecting to the bKash checkout,
    the user is shown a page with the bKash number to send money to.
    After sending, they submit the transaction ID. An admin email is sent
    for verification.
    """
    method_key = 'manual'
    is_redirect = False

    def create_payment(self, amount, reference, callback_url):
        """
        No external API call needed. Returns info for the manual checkout page.
        """
        return {
            "number": settings.MANUAL_PAYMENT_NUMBER,
            "amount": amount,
            "reference": reference,
        }

    def execute_payment(self, payment_id):
        """Not used for manual payments."""
        raise NotImplementedError("Manual payments are verified by admin, not via API.")

    @staticmethod
    def send_admin_notification(payment_attempt):
        """
        Sends an email to all admin/superusers notifying them of a new 
        manual payment that needs verification.
        """

        subject = f"[Cholbe AI] Manual Payment Verification Required - ৳{payment_attempt.amount}"
        message = (
            f"A manual payment has been submitted and needs your verification.\n\n"
            f"User: {payment_attempt.user.email}\n"
            f"Package: {payment_attempt.package.title if payment_attempt.package else 'N/A'}\n"
            f"Amount: ৳{payment_attempt.amount}\n"
            f"Transaction ID: {payment_attempt.manual_transaction_id}\n\n"
            f"Click the link below to verify this payment:\n"
            f"{payment_attempt.verify_url}\n\n"
            f"If this payment is fraudulent, you can reject it from the same page."
        )

        admin_email = settings.ADMIN_EMAIL
        if not admin_email:
            logger.warning("No admin emails found to send manual payment notification.")
            return

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
                fail_silently=False,
            )
            logger.info(f"Manual payment notification sent to {admin_email} for attempt {payment_attempt.id}")
        except Exception as e:
            logger.error(f"Failed to send manual payment notification: {e}")
