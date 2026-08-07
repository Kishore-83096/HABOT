from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import PaymentResultSerializer
from .services import apply_payment_result


class PaymentProcessAPIView(APIView):
    """Mock gateway endpoint used by clients during development."""

    def post(self, request):
        serializer = PaymentResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        payment, booking, availability = apply_payment_result(
            data["booking_id"], data["result"], data.get("gateway_reference", "")
        )
        return Response(payment_result_response(payment, booking, availability))


class PaymentWebhookAPIView(APIView):
    """Accept the same normalized payload a real payment gateway would send."""

    def post(self, request):
        serializer = PaymentResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        payment, booking, availability = apply_payment_result(
            data["booking_id"], data["result"], data.get("gateway_reference", "")
        )
        return Response(payment_result_response(payment, booking, availability))


def payment_result_response(payment, booking, availability):
    return {
        "booking_id": str(booking.id),
        "payment_id": str(payment.id),
        "booking_status": booking.status,
        "payment_status": payment.status,
        "availability_status": availability.status,
    }
