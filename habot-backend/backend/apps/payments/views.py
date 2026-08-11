from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from apps.common.responses import success_response

from .serializers import PaymentResultSerializer
from .services import apply_payment_result


class PaymentProcessAPIView(APIView):
    """Mock gateway endpoint used by clients during development."""

    @extend_schema(
        summary="Process a mock payment",
        description="Apply a simulated gateway success or failure result to a booking payment.",
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


def payment_result_response(payment, booking, availability):
    return {
        "booking_id": str(booking.id),
        "payment_id": str(payment.id),
        "booking_status": booking.status,
        "payment_status": payment.status,
        "availability_status": availability.status,
    }
