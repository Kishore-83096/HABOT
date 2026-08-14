from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from apps.bookings.models import Booking
from apps.lsas.models import Availability, LSAProfile, LSASkill, Skill
from apps.parents.models import Parent
from apps.payments.models import Payment


@pytest.mark.django_db
def test_bootstrap_creates_complete_discoverable_fixture(client):
    response = client.post("/api/v1/test-data/bootstrap/", {}, content_type="application/json")

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["test_run_id"].startswith("POSTMAN_TEST_")
    assert Parent.objects.filter(pk=data["parent"]["id"]).exists()
    assert LSAProfile.objects.filter(pk=data["lsa"]["id"], is_active=True).exists()
    assert Skill.objects.filter(pk=data["skills"][0]["id"]).exists()
    assert LSASkill.objects.filter(pk=data["lsa_skills"][0]["id"]).exists()
    assert Availability.objects.filter(pk=data["availability"][0]["id"], status=Availability.Status.AVAILABLE).exists()
    assert get_user_model().objects.filter(pk=data["admin"]["id"], is_staff=True, is_superuser=False).exists()

    search = client.get("/api/v1/lsas/search/", {"skill": data["skills"][0]["name"]})
    assert search.status_code == 200
    assert [item["id"] for item in search.json()["data"]] == [data["lsa"]["id"]]


@pytest.mark.django_db
def test_cleanup_removes_only_marked_test_fixture(client):
    bootstrap = client.post("/api/v1/test-data/bootstrap/", {}, content_type="application/json").json()["data"]
    unrelated_parent = Parent.objects.create(
        full_name="Real Parent",
        email="real@example.com",
        phone="1",
        city="Pune",
    )
    unrelated_lsa = LSAProfile.objects.create(full_name="Real LSA", hourly_rate=Decimal("500.00"))
    unrelated_skill = Skill.objects.create(name="Real Skill", category="Support")

    booking_response = client.post(
        "/api/v1/bookings/",
        {"parent_id": bootstrap["parent"]["id"], "availability_id": bootstrap["availability"][0]["id"]},
        content_type="application/json",
    )
    assert booking_response.status_code == 201

    response = client.delete(f"/api/v1/test-data/cleanup/{bootstrap['test_run_id']}/")

    assert response.status_code == 200
    deleted = response.json()["data"]["deleted"]
    assert deleted["parents"] == 1
    assert deleted["lsas"] == 1
    assert deleted["skills"] == 1
    assert deleted["availability"] == 2
    assert deleted["bookings"] == 1
    assert deleted["payments"] == 1
    assert Parent.objects.filter(pk=bootstrap["parent"]["id"]).exists() is False
    assert LSAProfile.objects.filter(pk=bootstrap["lsa"]["id"]).exists() is False
    assert Parent.objects.filter(pk=unrelated_parent.id).exists()
    assert LSAProfile.objects.filter(pk=unrelated_lsa.id).exists()
    assert Skill.objects.filter(pk=unrelated_skill.id).exists()


@pytest.mark.django_db
def test_repeated_bootstrap_runs_do_not_collide(client):
    first = client.post("/api/v1/test-data/bootstrap/", {}, content_type="application/json").json()["data"]
    second = client.post("/api/v1/test-data/bootstrap/", {}, content_type="application/json").json()["data"]

    assert first["test_run_id"] != second["test_run_id"]
    assert first["parent"]["id"] != second["parent"]["id"]
    assert first["lsa"]["id"] != second["lsa"]["id"]
    assert first["skills"][0]["name"] != second["skills"][0]["name"]


@pytest.mark.django_db
def test_cleanup_can_run_after_partial_failure(client):
    bootstrap = client.post("/api/v1/test-data/bootstrap/", {}, content_type="application/json").json()["data"]

    response = client.delete(f"/api/v1/test-data/cleanup/{bootstrap['test_run_id']}/")

    assert response.status_code == 200
    assert response.json()["data"]["deleted"]["bookings"] == 0
    assert Availability.objects.filter(pk=bootstrap["availability"][0]["id"]).exists() is False


@pytest.mark.django_db
def test_cleanup_rejects_non_test_run_ids(client):
    response = client.delete("/api/v1/test-data/cleanup/not-a-test-run/")

    assert response.status_code == 400
    assert response.json()["success"] is False


@pytest.mark.django_db
@override_settings(DEBUG=False, TEST_DATA_API_ENABLED=False)
def test_test_data_endpoints_are_disabled_when_configured_off(client):
    bootstrap = client.post("/api/v1/test-data/bootstrap/", {}, content_type="application/json")
    cleanup = client.delete("/api/v1/test-data/cleanup/POSTMAN_TEST_12345678/")

    assert bootstrap.status_code == 403
    assert cleanup.status_code == 403
