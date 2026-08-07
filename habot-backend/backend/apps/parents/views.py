from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response

from apps.bookings.serializers import BookingDetailSerializer
from apps.bookings.views import booking_queryset
from apps.bookings.models import Booking

from .models import Parent
from .serializers import ParentDetailSerializer, ParentListSerializer


class ParentListAPIView(generics.ListAPIView):
    """Return the mock parents available for selection."""

    queryset = Parent.objects.all()
    serializer_class = ParentListSerializer
    pagination_class = None


class ParentDetailAPIView(generics.RetrieveAPIView):
    queryset = Parent.objects.all()
    serializer_class = ParentDetailSerializer


class ParentBookingStatusAPIView(generics.GenericAPIView):
    """Return a parent's bookings with the latest payment status for refreshes."""

    def get(self, request, pk):
        get_object_or_404(Parent, pk=pk)
        bookings = booking_queryset().filter(parent_id=pk)
        booking_status = request.query_params.get("status")
        if booking_status:
            valid_statuses = {choice for choice, _ in Booking.Status.choices}
            if booking_status not in valid_statuses:
                return Response({"status": "Invalid booking status."}, status=400)
            bookings = bookings.filter(status=booking_status)
        return Response(BookingDetailSerializer(bookings, many=True).data)


class ParentDashboardAPIView(generics.GenericAPIView):
    def get(self, request, pk):
        get_object_or_404(Parent, pk=pk)
        counts = Booking.objects.filter(parent_id=pk).aggregate(
            total_bookings=Count("id"),
            upcoming=Count("id", filter=Q(status__in=[Booking.Status.PENDING, Booking.Status.PAYMENT_PENDING, Booking.Status.CONFIRMED])),
            completed=Count("id", filter=Q(status=Booking.Status.COMPLETED)),
            cancelled=Count("id", filter=Q(status=Booking.Status.CANCELLED)),
            failed=Count("id", filter=Q(status=Booking.Status.FAILED)),
        )
        return Response(counts)
