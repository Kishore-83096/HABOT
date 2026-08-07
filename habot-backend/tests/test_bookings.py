from datetime import time, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.bookings.models import Booking
from apps.lsas.models import Availability, LSAProfile
from apps.parents.models import Parent
from apps.payments.models import Payment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def parent():
    return Parent.objects.create(
        full_name="Asha Parent",
        email="asha@example.com",
        phone="1234567890",
        city="Bengaluru",
    )


@pytest.fixture
def availability():
    lsa = LSAProfile.objects.create(
        full_name="Maya LSA",
        hourly_rate=Decimal("800.00"),
        rating=Decimal("4.50"),
    )
    return Availability.objects.create(
        lsa=lsa,
        date=timezone.localdate() + timedelta(days=1),
        start_time=time(10, 0),
        end_time=time(11, 0),
    )


@pytest.mark.django_db
def test_successful_booking_creates_payment_and_reserves_slot(api_client, parent, availability):
    response = api_client.post(
        "/api/v1/bookings/",
        {"parent_id": str(parent.id), "availability_id": str(availability.id)},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["status"] == Booking.Status.PAYMENT_PENDING
    assert response.data["payment_status"] == Payment.Status.INITIATED
    availability.refresh_from_db()
    assert availability.status == Availability.Status.BOOKED
    payment = Payment.objects.get(booking_id=response.data["booking_id"])
    assert payment.amount == Decimal("800.00")


@pytest.mark.django_db
def test_reserved_slot_cannot_be_booked_again(api_client, parent, availability):
    payload = {"parent_id": str(parent.id), "availability_id": str(availability.id)}
    assert api_client.post("/api/v1/bookings/", payload, format="json").status_code == 201

    response = api_client.post("/api/v1/bookings/", payload, format="json")

    assert response.status_code == 400
    assert response.data["availability_id"] == "This slot is no longer available."


@pytest.mark.django_db
def test_invalid_parent_and_availability_return_not_found(api_client, parent):
    unknown_id = "00000000-0000-0000-0000-000000000001"
    invalid_parent = api_client.post(
        "/api/v1/bookings/",
        {"parent_id": unknown_id, "availability_id": unknown_id},
        format="json",
    )
    assert invalid_parent.status_code == 404

    invalid_availability = api_client.post(
        "/api/v1/bookings/",
        {"parent_id": str(parent.id), "availability_id": unknown_id},
        format="json",
    )
    assert invalid_availability.status_code == 404
