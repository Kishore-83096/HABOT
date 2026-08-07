from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lsas.models import Availability
from apps.parents.models import Parent
from apps.payments.models import Payment

from .models import Booking
from .serializers import BookingCreateSerializer, BookingDetailSerializer
from .services import cancel_booking


def booking_queryset():
    return Booking.objects.select_related("parent", "availability__lsa").prefetch_related(
        Prefetch("payments", queryset=Payment.objects.order_by("-transaction_time"), to_attr="prefetched_payments")
    )


def slot_is_in_the_past(availability):
    starts_at = datetime.combine(availability.date, availability.start_time)
    starts_at = timezone.make_aware(starts_at, timezone.get_current_timezone())
    return starts_at <= timezone.now()


def payment_amount(availability):
    start = datetime.combine(availability.date, availability.start_time)
    end = datetime.combine(availability.date, availability.end_time)
    duration_hours = Decimal(str((end - start).total_seconds())) / Decimal("3600")
    return (availability.lsa.hourly_rate * duration_hours).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


class BookingListCreateAPIView(APIView):
    def get(self, request):
        bookings = booking_queryset()
        return Response(BookingDetailSerializer(bookings, many=True).data)

    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parent_id = serializer.validated_data["parent_id"]
        availability_id = serializer.validated_data["availability_id"]

        try:
            parent = Parent.objects.get(pk=parent_id)
        except Parent.DoesNotExist as exc:
            raise NotFound({"parent_id": "Parent not found."}) from exc

        with transaction.atomic():
            try:
                availability = (
                    Availability.objects.select_for_update()
                    .select_related("lsa")
                    .get(pk=availability_id)
                )
            except Availability.DoesNotExist as exc:
                raise NotFound({"availability_id": "Availability slot not found."}) from exc

            if availability.status != Availability.Status.AVAILABLE:
                raise ValidationError({"availability_id": "This slot is no longer available."})
            if slot_is_in_the_past(availability):
                raise ValidationError({"availability_id": "This slot is in the past."})

            try:
                booking = Booking.objects.create(
                    parent=parent,
                    availability=availability,
                    status=Booking.Status.PAYMENT_PENDING,
                )
            except IntegrityError as exc:
                raise ValidationError({"availability_id": "This slot already has a booking."}) from exc

            availability.status = Availability.Status.BOOKED
            availability.save(update_fields=("status",))
            payment = Payment.objects.create(
                booking=booking,
                amount=payment_amount(availability),
                status=Payment.Status.INITIATED,
            )

        return Response(
            {
                "booking_id": str(booking.id),
                "status": booking.status,
                "payment_status": payment.status,
                "availability_id": str(availability.id),
            },
            status=status.HTTP_201_CREATED,
        )


class BookingDetailAPIView(APIView):
    def get(self, request, pk):
        try:
            booking = booking_queryset().get(pk=pk)
        except Booking.DoesNotExist as exc:
            raise NotFound("Booking not found.") from exc
        return Response(BookingDetailSerializer(booking).data)


class BookingCancelAPIView(APIView):
    def post(self, request, pk):
        try:
            cancel_booking(pk)
        except Booking.DoesNotExist as exc:
            raise NotFound("Booking not found.") from exc
        booking = booking_queryset().get(pk=pk)
        return Response(BookingDetailSerializer(booking).data)
