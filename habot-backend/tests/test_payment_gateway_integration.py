from datetime import time, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
import requests
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
def pending_booking(api_client):
    parent = Parent.objects.create(
        full_name="Gateway Parent", email="gateway@example.com", phone="9876543211", city="Pune"
    )
    lsa = LSAProfile.objects.create(full_name="Gateway LSA", hourly_rate=Decimal("600.00"))
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


def gateway_response(status_code=200, payload=None, http_error=None):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = payload or {}
    response.raise_for_status.side_effect = http_error
    return response


@pytest.mark.django_db
@patch("apps.payments.payment_gateway.requests.post")
def test_successful_external_payment_calls_gateway_and_confirms_booking(mock_post, api_client, pending_booking):
    mock_post.return_value = gateway_response(
        payload={"result": "success", "gateway_reference": "mock-gateway-success"}
    )

    response = api_client.post(
        "/api/v1/payments/process/", {"booking_id": str(pending_booking.id), "result": "success"}, format="json"
    )

    assert response.status_code == 200
    assert mock_post.called is True
    assert response.data["data"]["payment_status"] == Payment.Status.SUCCESS
    assert response.data["data"]["booking_status"] == Booking.Status.CONFIRMED


@pytest.mark.django_db
@patch("apps.payments.payment_gateway.requests.post")
def test_external_payment_failure_fails_booking_and_releases_slot(mock_post, api_client, pending_booking):
    mock_post.return_value = gateway_response(
        status_code=400,
        payload={"result": "failed", "gateway_reference": "mock-gateway-failed"},
    )

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
@patch("apps.payments.payment_gateway.requests.post")
@patch("apps.payments.payment_gateway.logger")
def test_payment_gateway_timeout_is_handled_without_mutating_state(
    mock_logger, mock_post, api_client, pending_booking
):
    mock_post.side_effect = requests.exceptions.Timeout

    response = api_client.post(
        "/api/v1/payments/process/", {"booking_id": str(pending_booking.id), "result": "success"}, format="json"
    )

    assert response.status_code == 503
    assert "timed out" in response.data["message"]
    assert any("Payment gateway request timed out" in call.args[0] for call in mock_logger.warning.call_args_list)
    pending_booking.refresh_from_db()
    payment = Payment.objects.get(booking=pending_booking)
    assert payment.status == Payment.Status.INITIATED
    assert pending_booking.status == Booking.Status.PAYMENT_PENDING


@pytest.mark.django_db
@patch("apps.payments.payment_gateway.requests.post")
def test_payment_gateway_connection_failure_is_handled(mock_post, api_client, pending_booking):
    mock_post.side_effect = requests.exceptions.ConnectionError

    response = api_client.post(
        "/api/v1/payments/process/", {"booking_id": str(pending_booking.id), "result": "success"}, format="json"
    )

    assert response.status_code == 503
    assert "connect" in response.data["message"]
    payment = Payment.objects.get(booking=pending_booking)
    assert payment.status == Payment.Status.INITIATED


@pytest.mark.django_db
@patch("apps.payments.payment_gateway.requests.post")
def test_payment_gateway_http_error_is_handled(mock_post, api_client, pending_booking):
    http_error = requests.exceptions.HTTPError(response=Mock(status_code=502))
    mock_post.return_value = gateway_response(
        status_code=502,
        payload={"detail": "bad gateway"},
        http_error=http_error,
    )

    response = api_client.post(
        "/api/v1/payments/process/", {"booking_id": str(pending_booking.id), "result": "success"}, format="json"
    )

    assert response.status_code == 503
    assert "HTTP error" in response.data["message"]
    payment = Payment.objects.get(booking=pending_booking)
    assert payment.status == Payment.Status.INITIATED


@pytest.mark.django_db
@patch("apps.payments.payment_gateway.requests.post")
def test_payment_gateway_request_uses_configured_timeout(mock_post, settings, api_client, pending_booking):
    settings.PAYMENT_GATEWAY_TIMEOUT = 3
    mock_post.return_value = gateway_response(
        payload={"result": "success", "gateway_reference": "mock-gateway-success"}
    )

    api_client.post(
        "/api/v1/payments/process/", {"booking_id": str(pending_booking.id), "result": "success"}, format="json"
    )

    mock_post.assert_called_once()
    assert mock_post.call_args.kwargs["timeout"] == 3
