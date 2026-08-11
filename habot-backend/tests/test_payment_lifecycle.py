from datetime import time, timedelta
from decimal import Decimal
from unittest.mock import Mock

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


@pytest.fixture(autouse=True)
def mock_payment_gateway(monkeypatch):
    def post(url, json, timeout):
        response = Mock()
        response.status_code = 200 if json["result"] == "success" else 400
        response.json.return_value = {
            "result": json["result"],
            "gateway_reference": json.get("gateway_reference", f"mock-gateway-{json['payment_id']}"),
        }
        response.raise_for_status.return_value = None
        return response

    monkeypatch.setattr("apps.payments.payment_gateway.requests.post", post)


@pytest.fixture
def pending_booking(api_client):
    parent = Parent.objects.create(
        full_name="Payment Parent", email="payment@example.com", phone="9876543210", city="Pune"
    )
    lsa = LSAProfile.objects.create(full_name="Payment LSA", hourly_rate=Decimal("500.00"))
    slot = Availability.objects.create(
        lsa=lsa,
        date=timezone.localdate() + timedelta(days=1),
        start_time=time(9),
        end_time=time(10),
    )
    response = api_client.post(
        "/api/v1/bookings/", {"parent_id": str(parent.id), "availability_id": str(slot.id)}, format="json"
    )
    assert response.status_code == 201
    return Booking.objects.get(pk=response.data["data"]["booking_id"])


@pytest.mark.django_db
def test_successful_payment_confirms_booking_and_keeps_slot_booked(api_client, pending_booking):
    response = api_client.post(
        "/api/v1/payments/process/", {"booking_id": str(pending_booking.id), "result": "success"}, format="json"
    )

    assert response.status_code == 200
    assert response.data["success"] is True
    assert response.data["data"]["payment_status"] == Payment.Status.SUCCESS
    assert response.data["data"]["booking_status"] == Booking.Status.CONFIRMED
    pending_booking.refresh_from_db()
    pending_booking.availability.refresh_from_db()
    assert pending_booking.availability.status == Availability.Status.BOOKED


@pytest.mark.django_db
def test_failed_payment_fails_booking_and_releases_slot(api_client, pending_booking):
    response = api_client.post(
        "/api/v1/payments/process/", {"booking_id": str(pending_booking.id), "result": "failed"}, format="json"
    )

    assert response.status_code == 200
    assert response.data["data"]["payment_status"] == Payment.Status.FAILED
    assert response.data["data"]["booking_status"] == Booking.Status.FAILED
    pending_booking.refresh_from_db()
    pending_booking.availability.refresh_from_db()
    assert pending_booking.availability.status == Availability.Status.AVAILABLE


@pytest.mark.django_db
def test_webhook_updates_payment_and_booking(api_client, pending_booking):
    response = api_client.post(
        "/api/v1/payments/webhook/",
        {"booking_id": str(pending_booking.id), "result": "success", "gateway_reference": "gateway-123"},
        format="json",
    )

    assert response.status_code == 200
    payment = Payment.objects.get(booking=pending_booking)
    pending_booking.refresh_from_db()
    assert payment.status == Payment.Status.SUCCESS
    assert payment.gateway_reference == "gateway-123"
    assert pending_booking.status == Booking.Status.CONFIRMED


@pytest.mark.django_db
def test_repeated_webhook_is_idempotent(api_client, pending_booking):
    payload = {"booking_id": str(pending_booking.id), "result": "failed"}
    first = api_client.post("/api/v1/payments/webhook/", payload, format="json")
    second = api_client.post("/api/v1/payments/webhook/", payload, format="json")

    assert first.status_code == second.status_code == 200
    assert second.data["data"]["payment_status"] == Payment.Status.FAILED
    assert Payment.objects.filter(booking=pending_booking).count() == 1
    pending_booking.refresh_from_db()
    pending_booking.availability.refresh_from_db()
    assert pending_booking.status == Booking.Status.FAILED
    assert pending_booking.availability.status == Availability.Status.AVAILABLE


@pytest.mark.django_db
def test_parent_booking_status_returns_latest_booking_and_payment(api_client, pending_booking):
    api_client.post(
        "/api/v1/payments/process/", {"booking_id": str(pending_booking.id), "result": "success"}, format="json"
    )

    response = api_client.get(f"/api/v1/parents/{pending_booking.parent_id}/bookings/")

    assert response.status_code == 200
    assert response.data["data"][0]["id"] == str(pending_booking.id)
    assert response.data["data"][0]["status"] == Booking.Status.CONFIRMED
    assert response.data["data"][0]["payment_status"] == Payment.Status.SUCCESS
