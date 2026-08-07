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
def booking_data():
    parent = Parent.objects.create(full_name="Dashboard Parent", email="dashboard@example.com", phone="1", city="Pune")
    lsa = LSAProfile.objects.create(full_name="Schedule LSA", hourly_rate=Decimal("500"))
    available = Availability.objects.create(lsa=lsa, date=timezone.localdate() + timedelta(days=1), start_time=time(9), end_time=time(10))
    booked = Availability.objects.create(lsa=lsa, date=timezone.localdate() + timedelta(days=1), start_time=time(10), end_time=time(11), status=Availability.Status.BOOKED)
    blocked = Availability.objects.create(lsa=lsa, date=timezone.localdate() + timedelta(days=2), start_time=time(9), end_time=time(10), status=Availability.Status.BLOCKED)
    booking = Booking.objects.create(parent=parent, availability=booked, status=Booking.Status.CONFIRMED)
    Payment.objects.create(booking=booking, amount=Decimal("500"), status=Payment.Status.SUCCESS)
    return parent, lsa, available, booked, blocked, booking


@pytest.mark.django_db
def test_parent_history_filter_and_booking_detail(api_client, booking_data):
    parent, _, _, _, _, booking = booking_data
    history = api_client.get(f"/api/v1/parents/{parent.id}/bookings/?status=CONFIRMED")
    detail = api_client.get(f"/api/v1/bookings/{booking.id}/")

    assert history.status_code == detail.status_code == 200
    assert history.data[0]["booking_id"] == str(booking.id)
    assert detail.data["lsa"]["name"] == "Schedule LSA"
    assert detail.data["slot"]["start_time"] == time(10)
    assert detail.data["payment_status"] == Payment.Status.SUCCESS


@pytest.mark.django_db
def test_cancellation_releases_slot_and_dashboard_counts(api_client, booking_data):
    parent, _, _, booked, _, booking = booking_data
    response = api_client.post(f"/api/v1/bookings/{booking.id}/cancel/")
    booked.refresh_from_db()
    summary = api_client.get(f"/api/v1/parents/{parent.id}/dashboard/")

    assert response.status_code == 200
    assert response.data["booking_status"] == Booking.Status.CANCELLED
    assert booked.status == Availability.Status.AVAILABLE
    assert summary.data == {"total_bookings": 1, "upcoming": 0, "completed": 0, "cancelled": 1, "failed": 0}


@pytest.mark.django_db
def test_schedule_returns_all_states_and_date_filter(api_client, booking_data):
    _, lsa, available, booked, blocked, _ = booking_data
    response = api_client.get(f"/api/v1/lsas/{lsa.id}/schedule/?date={available.date}")

    assert response.status_code == 200
    assert {item["id"] for item in response.data} == {str(available.id), str(booked.id)}
    assert {item["status"] for item in response.data} == {Availability.Status.AVAILABLE, Availability.Status.BOOKED}
    assert str(blocked.id) not in {item["id"] for item in response.data}
