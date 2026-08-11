from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from apps.common.responses import success_response
from apps.payments.models import Payment

from .models import Booking
from .serializers import BookingCreateSerializer, BookingDetailSerializer
from .services import cancel_booking, create_booking


def booking_queryset():
    return Booking.objects.select_related("parent", "availability__lsa").prefetch_related(
        Prefetch("payments", queryset=Payment.objects.order_by("-transaction_time"), to_attr="prefetched_payments")
    )


class BookingListCreateAPIView(APIView):
    @extend_schema(
        summary="List bookings",
        description="Return all bookings with parent, LSA, slot, and latest payment status details.",
    )
    def get(self, request):
        bookings = booking_queryset()
        return success_response(
            BookingDetailSerializer(bookings, many=True).data,
            message="Bookings retrieved successfully.",
        )

    @extend_schema(
        summary="Create a booking",
        description=(
            "Reserve an available future LSA slot for a mock parent and create an initiated "
            "payment record in the same database transaction."
        ),
        request=BookingCreateSerializer,
    )
    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking, payment, availability = create_booking(
            serializer.validated_data["parent_id"],
            serializer.validated_data["availability_id"],
        )
        return success_response(
            data={
                "booking_id": str(booking.id),
                "status": booking.status,
                "payment_status": payment.status,
                "availability_id": str(availability.id),
            },
            message="Booking created successfully.",
            status=status.HTTP_201_CREATED,
        )


class BookingDetailAPIView(APIView):
    @extend_schema(
        summary="Retrieve a booking",
        description="Return one booking with parent, LSA, slot, and latest payment status details.",
    )
    def get(self, request, pk):
        try:
            booking = booking_queryset().get(pk=pk)
        except Booking.DoesNotExist as exc:
            raise NotFound("Booking not found.") from exc
        return success_response(
            BookingDetailSerializer(booking).data,
            message="Booking retrieved successfully.",
        )


class BookingCancelAPIView(APIView):
    @extend_schema(
        summary="Cancel a booking",
        description="Cancel a pending, payment-pending, or confirmed booking and release its slot.",
    )
    def post(self, request, pk):
        try:
            cancel_booking(pk)
        except Booking.DoesNotExist as exc:
            raise NotFound("Booking not found.") from exc
        booking = booking_queryset().get(pk=pk)
        return success_response(
            BookingDetailSerializer(booking).data,
            message="Booking cancelled successfully.",
        )
