from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from apps.bookings.models import Booking
from apps.lsas.models import Availability, LSAProfile, LSASkill, Skill
from apps.parents.models import Parent


def make_lsa(index=1):
    return LSAProfile.objects.create(
        full_name=f"Optimized LSA {index}",
        hourly_rate=Decimal("40.00"),
        rating=Decimal("4.50"),
    )


@pytest.mark.django_db
def test_lsa_search_uses_a_constant_two_queries(django_assert_num_queries, client):
    autism = Skill.objects.create(name="Autism", category="Support")
    speech = Skill.objects.create(name="Speech", category="Support")
    for index in range(8):
        lsa = make_lsa(index)
        LSASkill.objects.create(lsa=lsa, skill=autism)
        LSASkill.objects.create(lsa=lsa, skill=speech)

    # One annotated LSA query and one prefetch query for all skills; this does
    # not grow with the number of LSAs returned.
    with django_assert_num_queries(2):
        response = client.get("/api/v1/lsas/search/")

    assert response.status_code == 200
    assert len(response.json()["data"]) == 8


@pytest.mark.django_db
def test_database_constraints_protect_skill_slot_and_booking_integrity():
    lsa = make_lsa()
    skill = Skill.objects.create(name="ADHD", category="Support")
    LSASkill.objects.create(lsa=lsa, skill=skill)
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            LSASkill.objects.create(lsa=lsa, skill=skill)

    with transaction.atomic():
        with pytest.raises(IntegrityError):
            Availability.objects.create(
                lsa=lsa, date=date.today(), start_time=time(10), end_time=time(9)
            )

    slot = Availability.objects.create(
        lsa=lsa, date=date.today() + timedelta(days=1), start_time=time(10), end_time=time(11)
    )
    parent = Parent.objects.create(full_name="Integrity Parent", email="integrity@example.com", phone="1", city="Pune")
    Booking.objects.create(parent=parent, availability=slot)
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            Booking.objects.create(parent=parent, availability=slot)


@pytest.mark.django_db
def test_openapi_schema_and_swagger_ui_are_exposed(client):
    schema = client.get("/api/schema/")
    docs = client.get("/api/docs/")

    assert schema.status_code == 200
    assert "/api/v1/bookings/" in schema.content.decode()
    assert docs.status_code == 200


@pytest.mark.django_db
def test_search_filters_experience_and_hourly_rate(client):
    qualified = make_lsa(1)
    qualified.experience_years = 6
    qualified.hourly_rate = Decimal("40.00")
    qualified.save()
    expensive = make_lsa(2)
    expensive.experience_years = 8
    expensive.hourly_rate = Decimal("90.00")
    expensive.save()

    response = client.get("/api/v1/lsas/search/", {"experience": 5, "hourly_rate_max": "50.00"})

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]] == [str(qualified.id)]


@pytest.mark.django_db
def test_missing_booking_returns_a_consistent_detail_error(client):
    response = client.get("/api/v1/bookings/00000000-0000-0000-0000-000000000001/")

    assert response.status_code == 404
    assert response.json()["success"] is False
    assert response.json()["message"] == "Booking not found."


@pytest.mark.django_db
def test_cannot_cancel_completed_booking(client):
    lsa = make_lsa()
    slot = Availability.objects.create(
        lsa=lsa, date=date.today() + timedelta(days=1), start_time=time(10), end_time=time(11)
    )
    parent = Parent.objects.create(full_name="Completed Parent", email="completed@example.com", phone="2", city="Pune")
    booking = Booking.objects.create(parent=parent, availability=slot, status=Booking.Status.COMPLETED)

    response = client.post(f"/api/v1/bookings/{booking.id}/cancel/")

    assert response.status_code == 400
    assert response.json()["success"] is False
    assert response.json()["message"] == "Only pending or confirmed bookings can be cancelled."


@pytest.mark.django_db
def test_schedule_rejects_an_invalid_date(client):
    response = client.get("/api/v1/lsas/00000000-0000-0000-0000-000000000001/schedule/?date=not-a-date")

    assert response.status_code == 400
    assert response.json()["success"] is False
    assert response.json()["message"] == "Use ISO-8601 date format (YYYY-MM-DD)."
