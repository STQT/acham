"""API views for OCTO payment processing."""

from __future__ import annotations

import logging
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from acham.orders.models import (
    Order,
    OrderStatus,
    OrderStatusHistory,
    PaymentTransaction,
    PaymentTransactionStatus,
)
from acham.orders.services.octo_service import OctoService

logger = logging.getLogger(__name__)


class PaymentInitiateView(APIView):
    """Initiate payment for an order."""

    permission_classes = (IsAuthenticated,)

    def post(self, request, order_id):
        """Initiate payment transaction with OCTO."""
        try:
            order = Order.objects.get(public_id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {"error": _("Order not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        if order.status != OrderStatus.PENDING_PAYMENT:
            return Response(
                {"error": _("Order is not in pending payment status.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if payment already exists
        existing_payment = PaymentTransaction.objects.filter(
            order=order,
            status__in=[
                PaymentTransactionStatus.PENDING,
                PaymentTransactionStatus.PREPARED,
                PaymentTransactionStatus.VERIFICATION_REQUIRED,
                PaymentTransactionStatus.PROCESSING,
            ],
        ).first()

        if existing_payment:
            return Response(
                {
                    "transaction_id": existing_payment.octo_transaction_id,
                    "payment_id": existing_payment.octo_payment_id,
                    "status": existing_payment.status,
                    "verification_url": existing_payment.verification_url,
                    "seconds_left": existing_payment.seconds_left,
                },
                status=status.HTTP_200_OK,
            )

        # Prepare basket items
        basket = []
        for item in order.items.all():
            basket_item = {
                "position_desc": item.product_name,
                "count": item.quantity,
                "price": float(item.unit_price),
                "spic": "00305001001000000",  # Default SPIC code
                "inn": "",  # Can be configured per product
                "package_code": "1425207",  # Default package code
                "nds": 1,  # VAT rate (1 = 12%)
            }
            basket.append(basket_item)

        # Prepare user data
        user_data = {
            "user_id": str(request.user.id),
            "phone": order.customer_phone or (getattr(request.user, "phone", "") or ""),
            "email": order.customer_email or (request.user.email or ""),
        }

        # Generate shop transaction ID
        shop_transaction_id = order.number

        # Build return and notify URLs
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:4200")
        return_url = f"{frontend_url}/profile?order={order.public_id}"
        notify_url = f"{request.build_absolute_uri('/')}api/payments/notify/"

        # Get language from request
        language = request.GET.get("language", "uz")
        if language not in ["uz", "ru", "en"]:
            language = "uz"

        try:
            # Call OCTO prepare_payment
            octo_response = OctoService.prepare_payment(
                shop_transaction_id=shop_transaction_id,
                total_sum=order.total_amount,
                user_data=user_data,
                basket=basket,
                return_url=return_url,
                notify_url=notify_url,
                language=language,
                description=f"Order {order.number}",
            )

            # Check for errors
            if octo_response.get("error"):
                error_code = octo_response.get("error")
                error_message = octo_response.get("errMessage", _("Payment preparation failed."))
                logger.error(f"OCTO prepare_payment error: {error_code} - {error_message}")

                payment_transaction = PaymentTransaction.objects.create(
                    order=order,
                    shop_transaction_id=shop_transaction_id,
                    status=PaymentTransactionStatus.FAILED,
                    amount=order.total_amount,
                    currency=order.currency,
                    request_payload={"user_data": user_data, "basket": basket},
                    response_payload=octo_response,
                    error_code=error_code,
                    error_message=error_message,
                )

                return Response(
                    {
                        "error": error_message,
                        "error_code": error_code,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Success - create payment transaction
            octo_data = octo_response.get("data", {})
            octo_transaction_id = octo_data.get("id")

            payment_transaction = PaymentTransaction.objects.create(
                order=order,
                shop_transaction_id=shop_transaction_id,
                octo_transaction_id=octo_transaction_id,
                status=PaymentTransactionStatus.PREPARED,
                amount=order.total_amount,
                currency=order.currency,
                request_payload={"user_data": user_data, "basket": basket},
                response_payload=octo_response,
            )

            return Response(
                {
                    "transaction_id": octo_transaction_id,
                    "status": payment_transaction.status,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error initiating payment: {e}", exc_info=True)
            return Response(
                {"error": _("Failed to initiate payment. Please try again.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PaymentConfirmView(APIView):
    """Confirm payment with card data."""

    permission_classes = (IsAuthenticated,)

    def post(self, request, order_id):
        """Confirm payment with card details."""
        try:
            order = Order.objects.get(public_id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {"error": _("Order not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        transaction_id = request.data.get("transaction_id")
        if not transaction_id:
            return Response(
                {"error": _("transaction_id is required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment_transaction = PaymentTransaction.objects.get(
                order=order,
                octo_transaction_id=transaction_id,
            )
        except PaymentTransaction.DoesNotExist:
            return Response(
                {"error": _("Payment transaction not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get card data
        card_data = {
            "card_number": request.data.get("card_number"),
            "expire": request.data.get("expire"),  # Format: MMYY
            "cardholder_name": request.data.get("cardholder_name", ""),
        }

        if not card_data["card_number"] or not card_data["expire"]:
            return Response(
                {"error": _("card_number and expire are required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Call OCTO pay
            octo_response = OctoService.pay(
                transaction_id=transaction_id,
                card_data=card_data,
            )

            payment_transaction.response_payload = octo_response
            payment_transaction.request_payload = {
                **payment_transaction.request_payload,
                "card_data": card_data,
            }

            if octo_response.get("error"):
                error_code = octo_response.get("error")
                error_message = octo_response.get("errMessage", _("Payment failed."))
                payment_transaction.status = PaymentTransactionStatus.FAILED
                payment_transaction.error_code = error_code
                payment_transaction.error_message = error_message
                payment_transaction.save()

                return Response(
                    {
                        "error": error_message,
                        "error_code": error_code,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Success - get verification info
            payment_transaction.status = PaymentTransactionStatus.PROCESSING
            payment_transaction.save()

            # Get verification info for OTP
            try:
                verification_response = OctoService.verification_info(transaction_id)
                if not verification_response.get("error"):
                    verification_data = verification_response.get("data", {})
                    payment_transaction.octo_payment_id = verification_data.get("id")
                    payment_transaction.verification_url = verification_data.get("verification_url", "")
                    payment_transaction.seconds_left = verification_data.get("secondsLeft")
                    payment_transaction.status = PaymentTransactionStatus.VERIFICATION_REQUIRED
                    payment_transaction.save()

                    return Response(
                        {
                            "payment_id": payment_transaction.octo_payment_id,
                            "verification_url": payment_transaction.verification_url,
                            "seconds_left": payment_transaction.seconds_left,
                            "status": payment_transaction.status,
                        },
                        status=status.HTTP_200_OK,
                    )
            except Exception as e:
                logger.warning(f"Could not get verification info: {e}")

            return Response(
                {
                    "status": payment_transaction.status,
                    "message": _("Payment is being processed."),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error confirming payment: {e}", exc_info=True)
            payment_transaction.status = PaymentTransactionStatus.FAILED
            payment_transaction.error_message = str(e)
            payment_transaction.save()

            return Response(
                {"error": _("Failed to confirm payment. Please try again.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PaymentVerifyOTPView(APIView):
    """Verify OTP code for payment."""

    permission_classes = (IsAuthenticated,)

    def post(self, request, order_id):
        """Verify OTP code."""
        try:
            order = Order.objects.get(public_id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {"error": _("Order not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        transaction_id = request.data.get("transaction_id")
        sms_key = request.data.get("sms_key")

        if not transaction_id or not sms_key:
            return Response(
                {"error": _("transaction_id and sms_key are required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment_transaction = PaymentTransaction.objects.get(
                order=order,
                octo_transaction_id=transaction_id,
            )
        except PaymentTransaction.DoesNotExist:
            return Response(
                {"error": _("Payment transaction not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            # Call OCTO check_sms_key
            octo_response = OctoService.check_sms_key(
                transaction_id=transaction_id,
                sms_key=sms_key,
            )

            payment_transaction.response_payload = octo_response

            if octo_response.get("error"):
                error_code = octo_response.get("error")
                error_message = octo_response.get("errMessage", _("OTP verification failed."))
                payment_transaction.error_code = error_code
                payment_transaction.error_message = error_message
                payment_transaction.save()

                return Response(
                    {
                        "error": error_message,
                        "error_code": error_code,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Success - payment will be confirmed via webhook
            payment_transaction.status = PaymentTransactionStatus.PROCESSING
            payment_transaction.save()

            return Response(
                {
                    "status": payment_transaction.status,
                    "message": _("OTP verified. Payment is being processed."),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error verifying OTP: {e}", exc_info=True)
            return Response(
                {"error": _("Failed to verify OTP. Please try again.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["POST"])
@permission_classes([AllowAny])
def payment_notify_view(request):
    """Webhook endpoint for OCTO payment notifications."""
    payload = request.data
    logger.info(f"OCTO webhook received: {payload}")

    transaction_id = payload.get("transaction_id") or payload.get("id")
    if not transaction_id:
        logger.error("OCTO webhook: missing transaction_id")
        return Response({"error": "transaction_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        payment_transaction = PaymentTransaction.objects.get(octo_transaction_id=transaction_id)
    except PaymentTransaction.DoesNotExist:
        logger.error(f"OCTO webhook: payment transaction not found: {transaction_id}")
        return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)

    # Update payment transaction
    payment_transaction.response_payload = payload
    payment_status = payload.get("status", "").lower()

    with transaction.atomic():
        if payment_status == "success" or payload.get("error") == 0:
            payment_transaction.status = PaymentTransactionStatus.SUCCESS
            payment_transaction.completed_at = timezone.now()

            # Update order status
            order = payment_transaction.order
            if order.status == OrderStatus.PENDING_PAYMENT:
                order.status = OrderStatus.PAYMENT_CONFIRMED
                order.paid_at = timezone.now()
                order.save(update_fields=["status", "paid_at", "updated_at"])

                OrderStatusHistory.objects.create(
                    order=order,
                    from_status=OrderStatus.PENDING_PAYMENT,
                    to_status=OrderStatus.PAYMENT_CONFIRMED,
                    note=_("Payment confirmed via OCTO"),
                    metadata={"payment_transaction_id": payment_transaction.id},
                )

        elif payment_status == "failed" or payload.get("error"):
            payment_transaction.status = PaymentTransactionStatus.FAILED
            payment_transaction.error_code = payload.get("error")
            payment_transaction.error_message = payload.get("errMessage", _("Payment failed"))
            payment_transaction.completed_at = timezone.now()

            # Update order status
            order = payment_transaction.order
            if order.status == OrderStatus.PENDING_PAYMENT:
                order.status = OrderStatus.PAYMENT_FAILED
                order.save(update_fields=["status", "updated_at"])

                OrderStatusHistory.objects.create(
                    order=order,
                    from_status=OrderStatus.PENDING_PAYMENT,
                    to_status=OrderStatus.PAYMENT_FAILED,
                    note=_("Payment failed via OCTO"),
                    metadata={"payment_transaction_id": payment_transaction.id},
                )

        payment_transaction.save()

    return Response({"status": "ok"}, status=status.HTTP_200_OK)


class PaymentStatusView(APIView):
    """Get payment status for an order."""

    permission_classes = (IsAuthenticated,)

    def get(self, request, order_id):
        """Get payment status."""
        try:
            order = Order.objects.get(public_id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {"error": _("Order not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        payment_transaction = PaymentTransaction.objects.filter(order=order).order_by("-created_at").first()

        if not payment_transaction:
            return Response(
                {
                    "status": "no_payment",
                    "message": _("No payment transaction found for this order."),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "transaction_id": payment_transaction.octo_transaction_id,
                "payment_id": payment_transaction.octo_payment_id,
                "status": payment_transaction.status,
                "verification_url": payment_transaction.verification_url,
                "seconds_left": payment_transaction.seconds_left,
                "error_code": payment_transaction.error_code,
                "error_message": payment_transaction.error_message,
            },
            status=status.HTTP_200_OK,
        )

