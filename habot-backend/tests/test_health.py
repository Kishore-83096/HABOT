from unittest.mock import patch


def test_health_check_reports_connected_database(client):
    with patch("config.urls.connection.cursor") as cursor:
        response = client.get("/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_health_check_reports_unavailable_database(client):
    with patch("config.urls.connection.cursor", side_effect=RuntimeError):
        response = client.get("/health/")

    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy", "database": "unavailable"}
