from unittest.mock import patch


def test_health_check_reports_connected_database(client):
    with patch("config.urls.connection.cursor") as cursor:
        response = client.get("/health/")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Application is ready.",
        "data": {"status": "ok", "database": "connected"},
    }


def test_health_check_reports_unavailable_database(client):
    with patch("config.urls.connection.cursor", side_effect=RuntimeError):
        response = client.get("/health/")

    assert response.status_code == 503
    assert response.json() == {
        "success": False,
        "message": "Application is not ready.",
        "errors": {"database": "unavailable"},
    }


def test_live_health_check(client):
    response = client.get("/health/live/")

    assert response.status_code == 200
    assert response.json()["data"] == {"status": "ok"}
    assert "X-Request-ID" in response
