from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.lsas.models import Availability

from .models import Booking


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
    return booking
