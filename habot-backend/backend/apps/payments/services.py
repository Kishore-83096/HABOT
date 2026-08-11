import logging

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.bookings.models import Booking
from apps.lsas.models import Availability

from .models import Payment

logger = logging.getLogger("apps.payments")


def latest_payment_for_booking(booking_id):
    """Return the current payment for a booking, or a useful 404 response."""
    try:
        return Payment.objects.filter(booking_id=booking_id).latest("transaction_time")
    except Payment.DoesNotExist as exc:
        if not Booking.objects.filter(pk=booking_id).exists():
            raise NotFound({"booking_id": "Booking not found."}) from exc
        raise NotFound({"booking_id": "Payment not found for this booking."}) from exc


@transaction.atomic
def apply_payment_result(booking_id, result, gateway_reference=""):
    """Apply a gateway outcome exactly once and keep booking and slot in sync.

    Gateway retries are expected.  Once a payment is terminal, later deliveries
    are intentionally no-ops, including a conflicting outcome.
    """
    payment_id = latest_payment_for_booking(booking_id).id
    payment = Payment.objects.select_for_update().get(pk=payment_id)
    booking = Booking.objects.select_for_update().get(pk=payment.booking_id)
    availability = Availability.objects.select_for_update().get(pk=booking.availability_id)

    if payment.status == Payment.Status.INITIATED:
        if result == "success":
            payment.status = Payment.Status.SUCCESS
            booking.status = Booking.Status.CONFIRMED
            availability.status = Availability.Status.BOOKED
        else:
            payment.status = Payment.Status.FAILED
            booking.status = Booking.Status.FAILED
            availability.status = Availability.Status.AVAILABLE

        if gateway_reference:
            payment.gateway_reference = gateway_reference
        payment.transaction_time = timezone.now()
        payment.save(update_fields=("status", "gateway_reference", "transaction_time"))
        booking.save(update_fields=("status", "updated_at"))
        availability.save(update_fields=("status",))
        log_method = logger.info if payment.status == Payment.Status.SUCCESS else logger.warning
        log_method(
            "Payment processed booking_id=%s payment_id=%s result=%s",
            booking.id,
            payment.id,
            result,
        )
    else:
        logger.info(
            "Payment webhook idempotent no-op booking_id=%s payment_id=%s current_status=%s requested_result=%s",
            booking.id,
            payment.id,
            payment.status,
            result,
        )

    return payment, booking, availability
