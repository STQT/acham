"""API views for OCTO payment processing."""

from __future__ import annotations

import logging
from decimal import Decimal
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

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
    CurrencyRate,
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
                PaymentTransaction.Status.PENDING,
                PaymentTransaction.Status.PREPARED,
                PaymentTransaction.Status.VERIFICATION_REQUIRED,
                PaymentTransaction.Status.PROCESSING,
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

        # Generate unique shop transaction ID
        import uuid
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8].upper()
        shop_transaction_id = f"ACH-{timestamp}-{unique_id}"

        # Build return and notify URLs
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:4200")
        # return_url - куда OCTO редиректит после успешной оплаты
        return_url = f"{frontend_url}/checkout/payment-callback?order_id={order.public_id}"
        notify_url = f"{request.build_absolute_uri('/')}api/payments/notify/"

        # Get language from request
        language = request.GET.get("language", "uz")
        if language not in ["uz", "ru", "en"]:
            language = "uz"

        # Get currency from request
        currency = request.GET.get("currency", order.currency)
        if currency not in ["UZS", "USD", "CLS"]:
            # Default to order currency or USD
            currency = order.currency if order.currency in ["UZS", "USD", "CLS"] else "USD"

        # Determine country from shipping address
        shipping_address = order.addresses.filter(address_type='shipping').first()
        country = shipping_address.country if shipping_address else None
        is_uzbekistan = country and (
            country.lower() in ["uzbekistan", "узбекистан", "o'zbekiston", "ozbekiston", "uzbek"]
        )
        
        logger.info(f"Payment initiation - Country: {country}, Is Uzbekistan: {is_uzbekistan}, Request currency: {currency}")

        # Determine payment methods based on country
        # If country is not Uzbekistan, only allow bank_card (Visa/Mastercard)
        if is_uzbekistan:
            payment_methods = [
                {"method": "bank_card"},
                {"method": "uzcard"},
                {"method": "humo"},
            ]
        else:
            # For non-Uzbekistan countries, only Visa/Mastercard
            payment_methods = [
                {"method": "bank_card"},
            ]

        # Determine currency for OCTO:
        # - OCTO accepts ONLY UZS (CLS may not be available for all shops/test mode)
        # - If order currency is already UZS (from price_uzs), use as-is
        # - Otherwise convert USD to UZS using exchange rate from database
        # Get USD to UZS exchange rate from database
        USD_TO_UZS_RATE = CurrencyRate.get_usd_rate()
        
        # Ensure is_uzbekistan is a boolean (not None)
        is_uzbekistan = bool(is_uzbekistan)
        
        # Always use UZS for OCTO API (CLS support may vary by shop/test mode)
        octo_currency = "UZS"
        
        # If order currency is UZS, it means prices were already set using price_uzs
        # No conversion needed - use amounts as-is
        if order.currency == "UZS":
            octo_total_sum = order.total_amount
            logger.info(f"Order already in UZS (using price_uzs): {octo_total_sum} UZS - no conversion needed")
            # Basket items already have correct prices in UZS from order.items.unit_price
        elif currency == "USD" or order.currency == "USD":
            # Convert USD to UZS
            octo_total_sum = order.total_amount * USD_TO_UZS_RATE
            logger.info(f"Converting USD to UZS: {order.total_amount} USD -> {octo_total_sum} UZS (rate: {USD_TO_UZS_RATE})")
            # Convert basket item prices from USD to UZS
            for basket_item in basket:
                if isinstance(basket_item.get("price"), (int, float)):
                    basket_item["price"] = float(Decimal(str(basket_item["price"])) * USD_TO_UZS_RATE)
        elif currency == "UZS":
            # Currency is already UZS, use as-is
            octo_total_sum = order.total_amount
            logger.info(f"Using currency UZS with amount: {octo_total_sum}")
        else:
            # Unknown currency, try to convert from order currency
            logger.warning(f"Unknown currency '{currency}', order currency: {order.currency}, defaulting to UZS")
            # If order currency is USD, convert to UZS
            if order.currency == "USD":
                octo_total_sum = order.total_amount * USD_TO_UZS_RATE
                logger.info(f"Converting {order.currency} to UZS: {order.total_amount} {order.currency} -> {octo_total_sum} UZS")
                # Convert basket item prices
                for basket_item in basket:
                    if isinstance(basket_item.get("price"), (int, float)):
                        basket_item["price"] = float(Decimal(str(basket_item["price"])) * USD_TO_UZS_RATE)
            else:
                octo_total_sum = order.total_amount
                logger.info(f"Using amount as-is: {octo_total_sum} UZS")
        
        # Final validation: ensure octo_currency is UZS (only supported currency)
        if octo_currency != "UZS":
            logger.warning(f"Currency '{octo_currency}' not supported by OCTO, forcing to UZS")
            octo_currency = "UZS"
        
        logger.info(f"Payment methods: {payment_methods}, OCTO currency: {octo_currency}")

        # Get current time in OCTO format for init_time using TIME_ZONE from settings
        # timezone.localtime() automatically uses settings.TIME_ZONE
        local_time = timezone.localtime(timezone.now())
        init_time = local_time.strftime("%Y-%m-%d %H:%M:%S")

        try:
            # Call OCTO prepare_payment with determined currency and payment methods
            octo_response = OctoService.prepare_payment(
                shop_transaction_id=shop_transaction_id,
                total_sum=octo_total_sum,
                user_data=user_data,
                basket=basket,
                return_url=return_url,
                notify_url=notify_url,
                language=language,
                currency=octo_currency,  # UZS or CLS depending on country
                description=f"Order {order.number}",
                init_time=init_time,
                payment_methods=payment_methods,  # Filtered based on country
            )
            logger.info(f"OCTO prepare_payment request data: {{'shop_transaction_id': {shop_transaction_id}, 'total_sum': {order.total_amount}, 'user_data': {user_data}, 'basket': {basket}, 'return_url': {return_url}, 'notify_url': {notify_url}, 'language': {language}, 'description': 'Order {order.number}'}}")
            logger.info(f"OCTO prepare_payment raw response: {octo_response}")

            # Check if response contains payment URL (success case)
            # OCTO может возвращать error: 1, но при этом в data есть octo_pay_url - это успешный ответ
            octo_data = octo_response.get("data") or {}
            octo_pay_url = octo_response.get("octo_pay_url") or (octo_data.get("octo_pay_url") if octo_data else None)

            # Если есть octo_pay_url, это успешный ответ (даже если error: 1)
            if octo_pay_url:
                logger.info(f"OCTO prepare_payment success: payment URL received - {octo_pay_url}")
                # Извлекаем transaction_id из URL
                # URL формат: https://pay2.octo.uz/pay/{transaction_id} или https://pay2.octo.uz/pay/{transaction_id}?language=uz
                # Убираем query параметры перед извлечением transaction_id
                url_without_params = octo_pay_url.split('?')[0]
                transaction_id_from_url = url_without_params.split('/')[-1] if url_without_params else None

                if not transaction_id_from_url:
                    logger.error("OCTO prepare_payment error: Could not extract transaction_id from URL")
                    return Response(
                        {"error": _("Failed to extract transaction ID from payment URL.")},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
                octo_transaction_id = transaction_id_from_url or octo_data.get("id") or octo_data.get("octo_payment_UUID")
                
                # Проверяем, что URL правильный формат (/pay/, а не /otp-form/)
                # Если OCTO вернул /otp-form/, заменяем на /pay/
                if '/otp-form/' in octo_pay_url:
                    logger.warning(f"OCTO returned otp-form URL, converting to pay URL: {octo_pay_url}")
                    # Заменяем /otp-form/ на /pay/
                    octo_pay_url = octo_pay_url.replace('/otp-form/', '/pay/')
                
                # Убираем дублирующиеся query параметры language
                parsed = urlparse(octo_pay_url)
                query_params = parse_qs(parsed.query)
                # Оставляем только один language параметр (берем первый)
                if 'language' in query_params:
                    query_params['language'] = [query_params['language'][0]]
                # Пересобираем URL без дублирующихся параметров
                new_query = urlencode(query_params, doseq=True)
                octo_pay_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
                
                # Проверяем, есть ли уже такая транзакция
                existing_payment = PaymentTransaction.objects.filter(
                    shop_transaction_id=shop_transaction_id
                ).first()
                
                if existing_payment:
                    # Обновляем существующую транзакцию
                    existing_payment.octo_transaction_id = octo_transaction_id or existing_payment.octo_transaction_id
                    existing_payment.verification_url = octo_pay_url
                    existing_payment.response_payload = octo_response
                    existing_payment.save()
                    
                    return Response(
                        {
                            "transaction_id": existing_payment.octo_transaction_id,
                            "payment_id": existing_payment.octo_payment_id,
                            "status": existing_payment.status,
                            "payment_url": octo_pay_url,  # URL для редиректа на страницу оплаты OCTO
                        },
                        status=status.HTTP_200_OK,
                    )
                
                # Создаем новую транзакцию
                payment_transaction = PaymentTransaction.objects.create(
                    order=order,
                    shop_transaction_id=shop_transaction_id,
                    octo_transaction_id=octo_transaction_id,
                    status=PaymentTransaction.Status.PREPARED,
                    amount=order.total_amount,
                    currency=currency,  # Store original currency from request
                    request_payload={
                        "user_data": user_data, 
                        "basket": basket,
                        "country": country,
                        "is_uzbekistan": is_uzbekistan,
                        "octo_currency": octo_currency,
                        "payment_methods": payment_methods,
                    },
                    response_payload=octo_response,
                    verification_url=octo_pay_url,
                )
                
                # Для одностадийной оплаты через платежную страницу OCTO
                # Возвращаем octo_pay_url для редиректа на страницу оплаты OCTO
                response_data = {
                    "transaction_id": octo_transaction_id,
                    "payment_id": payment_transaction.octo_payment_id,
                    "status": payment_transaction.status,
                    "payment_url": octo_pay_url,  # URL для редиректа на страницу оплаты OCTO
                }
                
                return Response(
                    response_data,
                    status=status.HTTP_201_CREATED,
                )

            # Check for errors (только если нет octo_pay_url)
            if octo_response.get("error"):
                error_code = octo_response.get("error")
                error_message = octo_response.get("errMessage", _("Payment preparation failed."))
                logger.error(f"OCTO prepare_payment error: {error_code} - {error_message}")

                # Check if payment already exists (OCTO returns this when payment was created by previous request)
                octo_data = octo_response.get("data") or {}
                if "This payment was created by previous request" in error_message and octo_data:
                    # Payment already exists, try to find it or create it with OCTO data
                    octo_transaction_id = octo_data.get("id") or octo_data.get("octo_payment_UUID")
                    # Получаем payment_url из ответа
                    existing_pay_url = octo_data.get("octo_pay_url") or octo_response.get("octo_pay_url")

                    # Check if we already have this transaction
                    existing_payment = PaymentTransaction.objects.filter(
                        shop_transaction_id=shop_transaction_id
                    ).first()

                    if existing_payment:
                        # Return existing payment with payment_url
                        return Response(
                            {
                                "transaction_id": existing_payment.octo_transaction_id,
                                "payment_id": existing_payment.octo_payment_id,
                                "status": existing_payment.status,
                                "payment_url": existing_payment.verification_url or existing_pay_url,
                            },
                            status=status.HTTP_200_OK,
                        )
                    else:
                        # Create payment transaction with OCTO data
                        payment_transaction = PaymentTransaction.objects.create(
                            order=order,
                            shop_transaction_id=shop_transaction_id,
                            octo_transaction_id=octo_transaction_id,
                            status=PaymentTransaction.Status.PREPARED,
                            amount=order.total_amount,
                            currency=currency,  # Store original currency from request
                            request_payload={
                                "user_data": user_data, 
                                "basket": basket,
                                "country": country,
                                "is_uzbekistan": is_uzbekistan,
                                "octo_currency": octo_currency,
                                "payment_methods": payment_methods,
                            },
                            response_payload=octo_response,
                            verification_url=existing_pay_url or "",
                        )

                        return Response(
                            {
                                "transaction_id": octo_transaction_id,
                                "status": payment_transaction.status,
                                "payment_url": existing_pay_url,
                            },
                            status=status.HTTP_201_CREATED,
                        )

                # Regular error handling
                payment_transaction = PaymentTransaction.objects.create(
                    order=order,
                    shop_transaction_id=shop_transaction_id,
                    status=PaymentTransaction.Status.FAILED,
                    amount=order.total_amount,
                    currency=currency,  # Use currency from request
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
            octo_data = octo_response.get("data") or {}
            octo_transaction_id = octo_data.get("id") or octo_data.get("octo_payment_UUID") if octo_data else None
            octo_payment_id = (octo_data.get("octo_payment_UUID") or octo_data.get("payment_id")) if octo_data else None

            payment_transaction = PaymentTransaction.objects.create(
                order=order,
                shop_transaction_id=shop_transaction_id,
                octo_transaction_id=octo_transaction_id,
                octo_payment_id=octo_payment_id,
                status=PaymentTransaction.Status.PREPARED,
                amount=order.total_amount,
                currency=currency,  # Store original currency from request
                request_payload={
                    "user_data": user_data, 
                    "basket": basket,
                    "country": country,
                    "is_uzbekistan": is_uzbekistan,
                    "octo_currency": octo_currency,
                    "payment_methods": payment_methods,
                },
                response_payload=octo_response,
            )

            # Для одностадийной оплаты через платежную страницу OCTO
            # Возвращаем octo_pay_url для редиректа на страницу оплаты OCTO
            response_data = {
                "transaction_id": octo_transaction_id,
                "payment_id": octo_payment_id,
                "status": payment_transaction.status,
                "payment_url": octo_pay_url,  # URL для редиректа на страницу оплаты OCTO
            }

            return Response(
                response_data,
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
                payment_transaction.status = PaymentTransaction.Status.FAILED
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

            # Handle different payment flows based on OCTO response or card type
            pay_data = octo_response.get("data", {})
            payment_status = pay_data.get("status")

            # Determine flow based on card type or OCTO response
            card_number = card_data.get("card_number", "")
            is_visa_mc = card_number.startswith("4") or card_number.startswith("5")

            if payment_status == "otp_required" or (is_visa_mc and OctoService._get_test_mode()):
                # Visa/MC flow: OCTO provides OTP form URL
                otp_url = pay_data.get("otp_url")
                # If OCTO didn't provide otp_url, construct it with transaction_id
                if not otp_url:
                    # Get language from request or default to 'uz'
                    language = request.GET.get("language", "uz")
                    if language not in ["uz", "ru", "en"]:
                        language = "uz"
                    # Construct OTP form URL with transaction_id and language
                    otp_url = f"https://pay2.octo.uz/pay/{transaction_id}?language={language}"
                payment_transaction.octo_payment_id = pay_data.get("id", transaction_id)
                payment_transaction.verification_url = otp_url
                payment_transaction.status = PaymentTransaction.Status.VERIFICATION_REQUIRED
                payment_transaction.save()

                return Response(
                    {
                        "payment_id": payment_transaction.octo_payment_id,
                        "verification_url": payment_transaction.verification_url,
                        "status": payment_transaction.status,
                        "flow": "redirect",  # Indicates redirect to OCTO OTP form
                    },
                    status=status.HTTP_200_OK,
                )

            # Uzcard/Humo flow or default: proceed with verification for SMS OTP
            payment_transaction.status = PaymentTransaction.Status.PROCESSING
            payment_transaction.save()

            # Get verification info for OTP
            try:
                verification_response = OctoService.verification_info(transaction_id)

                if verification_response.get("error"):
                    logger.warning(f"Verification info failed: {verification_response}")
                    if OctoService._get_test_mode():
                        logger.info("Test mode: verification failed, but proceeding")
                        # In test mode, still require OTP verification
                        payment_transaction.status = PaymentTransaction.Status.VERIFICATION_REQUIRED
                        payment_transaction.seconds_left = 300  # 5 minutes
                        payment_transaction.save()

                        return Response(
                            {
                                "payment_id": transaction_id,
                                "verification_url": None,
                                "seconds_left": 300,
                                "status": payment_transaction.status,
                                "flow": "sms",  # SMS OTP flow
                            },
                            status=status.HTTP_200_OK,
                        )
                    else:
                        # In production, this would be an error
                        error_code = verification_response.get("error")
                        error_message = verification_response.get("errMessage", _("Failed to get verification info."))
                        payment_transaction.status = PaymentTransaction.Status.FAILED
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
                else:
                    verification_data = verification_response.get("data", {})
                    seconds_left = verification_data.get("secondsLeft", 300)

                    # According to OCTO docs, if secondsLeft is 0, verification failed
                    if seconds_left == 0:
                        if OctoService._get_test_mode():
                            logger.warning("Test mode: secondsLeft is 0, proceeding anyway")
                            seconds_left = 300  # Reset for test mode
                        else:
                            payment_transaction.status = PaymentTransaction.Status.FAILED
                            payment_transaction.error_message = _("Payment verification failed - no time left for OTP.")
                            payment_transaction.save()

                            return Response(
                                {
                                    "error": _("Payment verification failed - OTP timeout."),
                                },
                                status=status.HTTP_400_BAD_REQUEST,
                            )

                    payment_transaction.octo_payment_id = verification_data.get("id", transaction_id)
                    payment_transaction.verification_url = verification_data.get("verification_url")
                    payment_transaction.seconds_left = seconds_left
                    payment_transaction.status = PaymentTransaction.Status.VERIFICATION_REQUIRED
                    payment_transaction.save()

                    return Response(
                        {
                            "payment_id": payment_transaction.octo_payment_id,
                            "verification_url": payment_transaction.verification_url,
                            "seconds_left": payment_transaction.seconds_left,
                            "status": payment_transaction.status,
                            "flow": "sms",  # SMS OTP flow
                        },
                        status=status.HTTP_200_OK,
                    )
            except Exception as e:
                logger.warning(f"Could not get verification info: {e}")
                if OctoService._get_test_mode():
                    # In test mode, provide default OTP verification
                    payment_transaction.status = PaymentTransaction.Status.VERIFICATION_REQUIRED
                    payment_transaction.seconds_left = 300
                    payment_transaction.save()

                    return Response(
                        {
                            "payment_id": transaction_id,
                            "verification_url": None,
                            "seconds_left": 300,
                            "status": payment_transaction.status,
                            "flow": "sms",
                        },
                        status=status.HTTP_200_OK,
                    )

            # If all else fails, return processing status
            return Response(
                {
                    "status": payment_transaction.status,
                    "message": _("Payment is being processed."),
                },
                status=status.HTTP_200_OK,
            )

            return Response(
                {
                    "status": payment_transaction.status,
                    "message": _("Payment is being processed."),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error confirming payment: {e}", exc_info=True)
            payment_transaction.status = PaymentTransaction.Status.FAILED
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
            payment_transaction.status = PaymentTransaction.Status.PROCESSING
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
def payment_notify(request):
    """Webhook endpoint for OCTO payment notifications."""
    import json
    
    # Логируем информацию о запросе
    logger.info("=" * 80)
    logger.info("OCTO WEBHOOK NOTIFICATION RECEIVED")
    logger.info("=" * 80)
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request path: {request.path}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Remote address: {request.META.get('REMOTE_ADDR', 'unknown')}")
    logger.info(f"User agent: {request.META.get('HTTP_USER_AGENT', 'unknown')}")
    
    # Логируем полный payload
    payload = request.data
    try:
        payload_json = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
        logger.info(f"OCTO webhook payload (JSON):\n{payload_json}")
    except Exception as e:
        logger.warning(f"Could not serialize payload to JSON: {e}")
        logger.info(f"OCTO webhook payload (raw): {payload}")
    
    # Логируем все ключи payload для отладки
    if isinstance(payload, dict):
        logger.info(f"Payload keys: {list(payload.keys())}")
        for key, value in payload.items():
            logger.info(f"  - {key}: {value} (type: {type(value).__name__})")
    
    # OCTO отправляет octo_payment_UUID или octo_payment_id как идентификатор транзакции
    # Также можно использовать shop_transaction_id для поиска
    transaction_id = (
        payload.get("octo_payment_UUID") or 
        payload.get("octo_payment_id") or 
        payload.get("transaction_id") or 
        payload.get("id")
    )
    
    shop_transaction_id = payload.get("shop_transaction_id")
    
    if not transaction_id and not shop_transaction_id:
        logger.error("=" * 80)
        logger.error("OCTO webhook ERROR: missing transaction identifier")
        logger.error(f"Available payload keys: {list(payload.keys()) if isinstance(payload, dict) else 'not a dict'}")
        logger.error("=" * 80)
        return Response({"error": "transaction identifier is required"}, status=status.HTTP_400_BAD_REQUEST)

    logger.info(f"Looking for payment transaction with octo_transaction_id: {transaction_id} or shop_transaction_id: {shop_transaction_id}")
    
    try:
        # Сначала пробуем найти по octo_transaction_id (octo_payment_UUID)
        if transaction_id:
            payment_transaction = PaymentTransaction.objects.get(octo_transaction_id=transaction_id)
        # Если не нашли, пробуем по shop_transaction_id
        elif shop_transaction_id:
            payment_transaction = PaymentTransaction.objects.get(shop_transaction_id=shop_transaction_id)
        else:
            raise PaymentTransaction.DoesNotExist("No transaction identifier provided")
            
        logger.info(f"Found payment transaction: ID={payment_transaction.id}, Order={payment_transaction.order.public_id}, Current status={payment_transaction.status}")
    except PaymentTransaction.DoesNotExist:
        logger.error("=" * 80)
        logger.error(f"OCTO webhook ERROR: payment transaction not found")
        logger.error(f"Transaction ID from payload: {transaction_id}")
        logger.error(f"Shop transaction ID from payload: {shop_transaction_id}")
        logger.error(f"Payload: {payload}")
        logger.error("=" * 80)
        return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)

    # Update payment transaction
    old_status = payment_transaction.status
    payment_transaction.response_payload = payload
    payment_status = payload.get("status", "").lower()
    error_code = payload.get("error")
    error_message = payload.get("errMessage") or payload.get("errorMessage")
    
    logger.info(f"Processing payment status update:")
    logger.info(f"  - Old status: {old_status}")
    logger.info(f"  - Payment status from payload: {payment_status}")
    logger.info(f"  - Error code: {error_code}")
    logger.info(f"  - Error message: {error_message}")
    logger.info(f"  - Order ID: {payment_transaction.order.public_id}")
    logger.info(f"  - Order number: {payment_transaction.order.number}")
    logger.info(f"  - Amount: {payment_transaction.amount} {payment_transaction.currency}")

    # Get payment amount from webhook payload
    # OCTO sends total_sum in the payment currency (UZS or CLS)
    payment_amount_from_webhook = payload.get("total_sum")
    payment_currency_from_webhook = payload.get("currency", "UZS")
    
    # If payment was in UZS but order currency is USD, convert back to USD for storage
    order = payment_transaction.order
    if payment_currency_from_webhook == "UZS" and order.currency == "USD" and payment_amount_from_webhook:
        # Convert UZS amount back to USD
        usd_rate = CurrencyRate.get_usd_rate()
        converted_amount = Decimal(str(payment_amount_from_webhook)) / usd_rate
        payment_transaction.amount = converted_amount
        payment_transaction.currency = "USD"  # Store in order's original currency
        logger.info(f"Converted payment amount from UZS to USD: {payment_amount_from_webhook} UZS -> {converted_amount} USD (rate: {usd_rate})")
    elif payment_amount_from_webhook:
        # For CLS or if currencies match, use the amount as-is
        payment_transaction.amount = Decimal(str(payment_amount_from_webhook))
        payment_transaction.currency = order.currency
        logger.info(f"Payment amount: {payment_transaction.amount} {payment_transaction.currency} (no conversion needed)")

    with transaction.atomic():
        # OCTO отправляет статус "succeeded" при успешной оплате
        # Проверяем успешность: статус "succeeded" или "success", или error_code == 0
        is_success = (
            payment_status in ["success", "succeeded"] or 
            (error_code is not None and error_code == 0)
        )
        
        # Определяем финальный статус платежа
        if is_success:
            logger.info("Processing SUCCESS status")
            payment_transaction.status = PaymentTransaction.Status.SUCCESS
            payment_transaction.completed_at = timezone.now()
            
            # Сохраняем octo_payment_UUID если его еще нет (на случай если он не был сохранен при создании)
            if not payment_transaction.octo_transaction_id and transaction_id:
                payment_transaction.octo_transaction_id = transaction_id
            
            # Сохраняем octo_payment_id из payload если его еще нет
            if not payment_transaction.octo_payment_id and transaction_id:
                payment_transaction.octo_payment_id = transaction_id

            # Update order status (order variable already set above during amount conversion)
            old_order_status = order.status
            logger.info(f"Order status update: {old_order_status} -> PAYMENT_CONFIRMED")
            
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

                logger.info(f"Order {order.public_id} status updated to PAYMENT_CONFIRMED")
                logger.info(f"Order paid_at set to: {order.paid_at}")

                # Send order confirmation notification (email or SMS)
                try:
                    from acham.orders.tasks import send_order_notification
                    send_order_notification.delay(order.id)
                    logger.info(f"Order confirmation notification task queued for order {order.id}")
                except Exception as e:
                    logger.error(f"Failed to queue order notification: {e}", exc_info=True)
            else:
                logger.warning(f"Order {order.public_id} status is {old_order_status}, not updating to PAYMENT_CONFIRMED")

        elif payment_status in ["failed", "cancelled"] or (error_code and error_code != 0):
            logger.info("Processing FAILED status")
            payment_transaction.status = PaymentTransaction.Status.FAILED
            payment_transaction.error_code = str(error_code) if error_code else None
            payment_transaction.error_message = error_message or _("Payment failed")
            payment_transaction.completed_at = timezone.now()

            logger.info(f"Payment transaction marked as FAILED:")
            logger.info(f"  - Error code: {error_code}")
            logger.info(f"  - Error message: {payment_transaction.error_message}")

            # Update order status
            order = payment_transaction.order
            old_order_status = order.status
            logger.info(f"Order status update: {old_order_status} -> PAYMENT_FAILED")
            
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

                logger.info(f"Order {order.public_id} status updated to PAYMENT_FAILED")
            else:
                logger.warning(f"Order {order.public_id} status is {old_order_status}, not updating to PAYMENT_FAILED")
        else:
            logger.warning(f"Unknown payment status: {payment_status}, error_code: {error_code}")
            logger.warning(f"Payload: {payload}")

        payment_transaction.save()
        logger.info(f"Payment transaction saved with new status: {payment_transaction.status}")

    logger.info("=" * 80)
    logger.info("OCTO WEBHOOK PROCESSING COMPLETED")
    logger.info("=" * 80)
    
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

