from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CreditPackage, CreditTransaction, PaymentAttempt
from apps.core.models import SiteConfig
from .gateways import get_payment_adapter
from .gateways.manual import ManualPaymentAdapter
from .utils import build_payment_gtm_event
from django.conf import settings
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib import messages
from django.contrib import admin
from django.db import transaction
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@login_required
def buy_credit(request):
    packages = CreditPackage.objects.filter(is_active=True)
    using_overview_data = CreditTransaction.using_overview_data_list(user=request.user)
    site_config = SiteConfig.get_solo()
    context = admin.site.each_context(request)
    context.update({
        "title": "Credit",
        "packages": packages,
        "using_overview_data": using_overview_data,
        "credit_per_reply": site_config.credit_per_reply,
        "credit_per_comment": site_config.credit_per_comment,

    })
    return render(request, "credit/buy_credits.html", context)


@login_required
def checkout(request, package_id):
    package = get_object_or_404(CreditPackage, id=package_id, is_active=True)
    adapter = get_payment_adapter()

    payment_attempt, created = PaymentAttempt.objects.get_or_create(
        user=request.user,
        amount=package.price_bdt,
        package=package,
        payment_method=adapter.method_key,
        status="pending",
        manual_transaction_id=None,
    )

    reference = str(payment_attempt.id)

    if adapter.is_redirect:
        base_callback_url = request.build_absolute_uri(
            reverse('credit:payment_callback')
        )
        callback_url = f"{base_callback_url}?{urlencode({'reference': reference})}"
        payment_info = adapter.create_payment(
            amount=package.price_bdt,
            reference=reference,
            callback_url=callback_url,
        )
        return redirect(payment_info.get("redirectURL"))

    else:
        payment_info = adapter.create_payment(
            amount=package.price_bdt,
            reference=reference,
            callback_url=None,
        )
        context = admin.site.each_context(request)
        context.update({
            "title": "Manual Payment",
            "package": package,
            "payment_attempt": payment_attempt,
            "number": payment_info["number"],
            "amount": payment_info["amount"],
        })
        return render(request, "credit/manual_checkout.html", context)


@login_required
def payment_callback(request):
    """Callback for the bKash automatic adapter."""
    payment_id = request.GET.get("paymentID")
    status = request.GET.get("status")

    adapter = get_payment_adapter()
    result = adapter.execute_payment(payment_id)

    if result.get("statusCode") in ("0000", "2062"):
        reference = result.get("merchantInvoiceNumber") or request.GET.get("reference")

        if reference:
            with transaction.atomic():
                payment_attempt = PaymentAttempt.objects.select_for_update().get(
                    id=reference, user=request.user,
                )
                if payment_attempt.status == 'success':
                    return redirect("credit:buy_credit")

                package = payment_attempt.package
                if package:
                    payment_attempt.success()
                    request.session['gtm_payment_success'] = build_payment_gtm_event(payment_attempt)
                    messages.success(
                        request,
                        f"{package.credits} credits successfully added to your account!",
                    )
                    return redirect("credit:buy_credit")

    messages.error(request, "Payment verification failed.")
    return redirect("credit:buy_credit")



@login_required
def submit_transaction_id(request, attempt_id):
    """User submits the bKash transaction ID after sending money."""
    if request.method != "POST":
        return redirect("credit:buy_credit")

    payment_attempt = get_object_or_404(
        PaymentAttempt,
        id=attempt_id,
        user=request.user,
        payment_method='manual',
        status='pending',
    )

    trx_id = request.POST.get("transaction_id", "").strip()
    if not trx_id:
        messages.error(request, "Please enter a valid transaction ID.")
        return redirect("credit:checkout", package_id=payment_attempt.package.id)

    payment_attempt.manual_transaction_id = trx_id
    payment_attempt.save()
    ManualPaymentAdapter.send_admin_notification(payment_attempt)
    logger.info(f"Manual payment submitted: attempt={payment_attempt.id}, trx_id={trx_id}")
    messages.success(
        request,
        "Your payment has been submitted! We will verify the transaction "
        "and add credits to your account shortly.",
    )
    return redirect("credit:buy_credit")


@login_required
def admin_verify_payment(request, attempt_id):
    """
    Admin‑only view to verify or reject a manual payment.
    """
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to verify payments.")
        return redirect("credit:buy_credit")

    payment_attempt = get_object_or_404(PaymentAttempt, id=attempt_id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve" and payment_attempt.status == 'pending':
            with transaction.atomic():
                pa = PaymentAttempt.objects.select_for_update().get(id=attempt_id)
                if pa.status != 'pending':
                    messages.warning(request, "This payment has already been processed.")
                    return redirect("credit:buy_credit")

                package = pa.package
                if package and pa.user:
                    pa.success()
                    pa.user.notify(
                        type='success',
                        title='Payment Verified',
                        message=(
                            f'Your manual payment of ৳{pa.amount} has been verified. '
                            f'{package.credits} credits have been added to your account!'
                        ),
                    )

                    logger.info(f"Manual payment approved: attempt={pa.id}, user={pa.user.email}")
                    messages.success(
                        request,
                        f"Payment verified! {package.credits} credits added to {pa.user.email}.",
                    )
                else:
                    messages.error(request, "Could not process: package or user not found.")

        elif action == "reject" and payment_attempt.status == 'pending':
            payment_attempt.fail()

            if payment_attempt.user:
                payment_attempt.user.notify(
                    type='error',
                    title='Payment Rejected',
                    message=(
                        f'Your manual payment of ৳{payment_attempt.amount} '
                        f'(TrxID: {payment_attempt.manual_transaction_id}) could not be '
                        f'verified and has been rejected. Please contact support if you '
                        f'believe this is an error.'
                    ),
                )

            logger.info(f"Manual payment rejected: attempt={payment_attempt.id}")
            messages.info(request, "Payment has been rejected.")
        else:
            messages.warning(request, "This payment has already been processed.")

        return redirect("credit:buy_credit")

    # GET: show verification page
    context = admin.site.each_context(request)
    context.update({
        "title": "Verify Manual Payment",
        "payment_attempt": payment_attempt,
    })
    return render(request, "credit/admin_verify_payment.html", context)
