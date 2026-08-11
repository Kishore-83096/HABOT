import logging

import requests
from django.conf import settings
from rest_framework.exceptions import APIException

logger = logging.getLogger("apps.payments")


class PaymentGatewayError(APIException):
    status_code = 503
    default_detail = "Payment gateway is currently unavailable."
    default_code = "payment_gateway_unavailable"


def charge_payment(payment, requested_result):
    payload = {
        "payment_id": str(payment.id),
        "booking_id": str(payment.booking_id),
        "amount": str(payment.amount),
        "currency": "INR",
        "result": requested_result,
    }
    url = f"{settings.PAYMENT_GATEWAY_URL.rstrip('/')}/payments/"

    logger.info(
        "Sending payment request to mock payment gateway booking_id=%s payment_id=%s",
        payment.booking_id,
        payment.id,
    )

    try:
        response = requests.post(url, json=payload, timeout=settings.PAYMENT_GATEWAY_TIMEOUT)

        if response.status_code == 400:
            response_data = _gateway_result(_response_json(response))
            if response_data.get("result") != "failed":
                response.raise_for_status()
            logger.warning(
                "Mock payment gateway rejected payment booking_id=%s payment_id=%s",
                payment.booking_id,
                payment.id,
            )
            return response_data

        response.raise_for_status()
        response_data = _gateway_result(_response_json(response))
    except requests.exceptions.Timeout as exc:
        logger.warning(
            "Payment gateway request timed out booking_id=%s payment_id=%s",
            payment.booking_id,
            payment.id,
        )
        raise PaymentGatewayError("Payment gateway request timed out.") from exc
    except requests.exceptions.ConnectionError as exc:
        logger.warning(
            "Unable to connect to payment gateway booking_id=%s payment_id=%s",
            payment.booking_id,
            payment.id,
        )
        raise PaymentGatewayError("Unable to connect to payment gateway.") from exc
    except requests.exceptions.HTTPError as exc:
        logger.warning(
            "Payment gateway returned HTTP error booking_id=%s payment_id=%s status_code=%s",
            payment.booking_id,
            payment.id,
            getattr(exc.response, "status_code", response.status_code if "response" in locals() else None),
        )
        raise PaymentGatewayError("Payment gateway returned an HTTP error.") from exc
    except requests.exceptions.RequestException as exc:
        logger.warning(
            "Unexpected payment gateway request error booking_id=%s payment_id=%s",
            payment.booking_id,
            payment.id,
        )
        raise PaymentGatewayError("Payment gateway request failed.") from exc

    logger.info(
        "Mock payment gateway returned successful response booking_id=%s payment_id=%s result=%s",
        payment.booking_id,
        payment.id,
        response_data.get("result"),
    )
    return response_data


def _response_json(response):
    try:
        data = response.json()
    except ValueError as exc:
        logger.warning("Payment gateway returned invalid JSON status_code=%s", response.status_code)
        raise PaymentGatewayError("Payment gateway returned an invalid response.") from exc

    if not isinstance(data, dict):
        raise PaymentGatewayError("Payment gateway returned an invalid response.")
    return data


def _gateway_result(data):
    result_data = data.get("data", data)
    if not isinstance(result_data, dict) or result_data.get("result") not in ("success", "failed"):
        raise PaymentGatewayError("Payment gateway returned an invalid response.")
    return result_data
