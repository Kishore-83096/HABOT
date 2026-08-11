from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.exceptions import ValidationError

from apps.bookings.models import Booking
from apps.bookings.serializers import BookingDetailSerializer
from apps.bookings.views import booking_queryset
from apps.common.responses import EnvelopedListMixin, EnvelopedRetrieveMixin, success_response

from .models import Parent
from .serializers import ParentDetailSerializer, ParentListSerializer


class ParentListAPIView(EnvelopedListMixin, generics.ListAPIView):
    """Return the mock parents available for selection."""

    queryset = Parent.objects.all()
    serializer_class = ParentListSerializer
    pagination_class = None
    success_message = "Parents retrieved successfully."


class ParentDetailAPIView(EnvelopedRetrieveMixin, generics.RetrieveAPIView):
    queryset = Parent.objects.all()
    serializer_class = ParentDetailSerializer
    success_message = "Parent retrieved successfully."


class ParentBookingStatusAPIView(generics.GenericAPIView):
    """Return a parent's bookings with the latest payment status for refreshes."""

    @extend_schema(
        summary="List parent bookings",
        description="Return a parent's booking history, optionally filtered by booking status.",
    )
    def get(self, request, pk):
        get_object_or_404(Parent, pk=pk)
        bookings = booking_queryset().filter(parent_id=pk)
        booking_status = request.query_params.get("status")
        if booking_status:
            valid_statuses = {choice for choice, _ in Booking.Status.choices}
            if booking_status not in valid_statuses:
                raise ValidationError({"status": "Invalid booking status."})
            bookings = bookings.filter(status=booking_status)
        return success_response(
            BookingDetailSerializer(bookings, many=True).data,
            message="Parent bookings retrieved successfully.",
        )


class ParentDashboardAPIView(generics.GenericAPIView):
    @extend_schema(
        summary="Retrieve parent dashboard",
        description="Return booking counts for a mock parent dashboard.",
    )
    def get(self, request, pk):
        get_object_or_404(Parent, pk=pk)
        counts = Booking.objects.filter(parent_id=pk).aggregate(
            total_bookings=Count("id"),
            upcoming=Count(
                "id",
                filter=Q(
                    status__in=[
                        Booking.Status.PENDING,
                        Booking.Status.PAYMENT_PENDING,
                        Booking.Status.CONFIRMED,
                    ]
                ),
            ),
            completed=Count("id", filter=Q(status=Booking.Status.COMPLETED)),
            cancelled=Count("id", filter=Q(status=Booking.Status.CANCELLED)),
            failed=Count("id", filter=Q(status=Booking.Status.FAILED)),
        )
        return success_response(counts, message="Parent dashboard retrieved successfully.")
