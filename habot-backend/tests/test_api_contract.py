import pytest


@pytest.mark.django_db
def test_success_responses_use_global_contract(client):
    response = client.get("/api/v1/parents/")

    assert response.status_code == 200
    assert response.json().keys() == {"success", "message", "data"}
    assert response.json()["success"] is True
    assert "X-Request-ID" in response


@pytest.mark.django_db
def test_error_responses_use_global_contract(client):
    response = client.get(
        "/api/v1/bookings/00000000-0000-0000-0000-000000000001/"
    )

    assert response.status_code == 404
    assert response.json().keys() == {"success", "message", "errors"}
    assert response.json()["success"] is False
    assert response.json()["message"] == "Booking not found."
    assert "X-Request-ID" in response


def test_client_supplied_request_id_is_returned(client):
    response = client.get(
        "/health/live/",
        headers={"X-Request-ID": "contract-test-request"},
    )

    assert response["X-Request-ID"] == "contract-test-request"
