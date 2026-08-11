from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.views import APIView

from apps.common.responses import success_response

from .serializers import MockPaymentGatewaySerializer, PaymentResultSerializer
from .services import apply_payment_result, process_payment


class PaymentProcessAPIView(APIView):
    """Process a booking payment through the configured mock gateway client."""

    @extend_schema(
        summary="Process a mock payment",
        description="Apply a simulated gateway success or failure result to a booking payment.",
        request=PaymentResultSerializer,
    )
    def post(self, request):
        serializer = PaymentResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        payment, booking, availability = process_payment(data["booking_id"], data["result"])
        return success_response(
            payment_result_response(payment, booking, availability),
            message="Payment processed successfully.",
        )


class PaymentWebhookAPIView(APIView):
    """Accept the same normalized payload a real payment gateway would send."""

    @extend_schema(
        summary="Receive payment webhook",
        description=(
            "Apply a normalized gateway webhook payload. Processing is idempotent: "
            "repeated terminal-state notifications do not mutate the transaction again."
        ),
        request=PaymentResultSerializer,
    )
    def post(self, request):
        serializer = PaymentResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        payment, booking, availability = apply_payment_result(
            data["booking_id"], data["result"], data.get("gateway_reference", "")
        )
        return success_response(
            payment_result_response(payment, booking, availability),
            message="Payment webhook processed successfully.",
        )


class MockPaymentGatewayAPIView(APIView):
    """Small mock HTTP gateway used by the payment client integration."""

    @extend_schema(
        summary="Mock external payment gateway",
        description=(
            "Development-only mock gateway endpoint. The payment service calls this endpoint "
            "over HTTP using Python requests; clients normally use /api/v1/payments/process/."
        ),
        request=MockPaymentGatewaySerializer,
    )
    def post(self, request):
        serializer = MockPaymentGatewaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        gateway_reference = f"mock-gateway-{data['payment_id']}"
        response_data = {
            "result": data["result"],
            "gateway_reference": gateway_reference,
        }

        if data["result"] == "failed":
            return success_response(
                response_data,
                message="Mock payment gateway rejected payment.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        return success_response(
            response_data,
            message="Mock payment gateway approved payment.",
        )


def payment_result_response(payment, booking, availability):
    return {
        "booking_id": str(booking.id),
        "payment_id": str(payment.id),
        "booking_status": booking.status,
        "payment_status": payment.status,
        "availability_status": availability.status,
    }
