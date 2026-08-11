import logging
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from apps.lsas.models import Availability
from apps.parents.models import Parent
from apps.payments.models import Payment

from .models import Booking

logger = logging.getLogger("apps.bookings")


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


@transaction.atomic
def create_booking(parent_id, availability_id):
    try:
        parent = Parent.objects.get(pk=parent_id)
    except Parent.DoesNotExist as exc:
        raise NotFound({"parent_id": "Parent not found."}) from exc

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

    logger.info(
        "Booking created booking_id=%s parent_id=%s availability_id=%s payment_id=%s",
        booking.id,
        parent.id,
        availability.id,
        payment.id,
    )
    return booking, payment, availability


@transaction.atomic
def cancel_booking(booking_id):
    """Cancel an active booking and return its slot to the schedule."""
    booking = (
        Booking.objects.select_for_update()
        .select_related("availability")
        .get(pk=booking_id)
    )
    if booking.status not in (Booking.Status.PENDING, Booking.Status.CONFIRMED, Booking.Status.PAYMENT_PENDING):
        raise ValidationError({"status": "Only pending or confirmed bookings can be cancelled."})

    availability = Availability.objects.select_for_update().get(pk=booking.availability_id)
    booking.status = Booking.Status.CANCELLED
    availability.status = Availability.Status.AVAILABLE
    booking.save(update_fields=("status", "updated_at"))
    availability.save(update_fields=("status",))
    logger.info("Booking cancelled booking_id=%s availability_id=%s", booking.id, availability.id)
    return booking
