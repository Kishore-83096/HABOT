from datetime import date, time
from decimal import Decimal

import pytest

from apps.lsas.models import Availability, LSAProfile, LSASkill, Skill
from apps.parents.models import Parent


@pytest.fixture
def parent():
    return Parent.objects.create(
        full_name="John Doe",
        email="john@example.com",
        phone="1234567890",
        city="London",
    )


@pytest.fixture
def lsa():
    profile = LSAProfile.objects.create(
        full_name="Alice",
        bio="Experienced learning support assistant.",
        experience_years=8,
        rating=Decimal("4.80"),
        hourly_rate=Decimal("60.00"),
    )
    autism = Skill.objects.create(name="Autism", category="Support")
    speech = Skill.objects.create(name="Speech Therapy", category="Therapy")
    LSASkill.objects.create(lsa=profile, skill=autism, experience_years=8)
    LSASkill.objects.create(lsa=profile, skill=speech, experience_years=5)
    return profile


@pytest.mark.django_db
def test_list_and_retrieve_parent(client, parent):
    list_response = client.get("/api/v1/parents/")
    detail_response = client.get(f"/api/v1/parents/{parent.id}/")

    assert list_response.status_code == 200
    assert list_response.json()["data"] == [{"id": str(parent.id), "full_name": "John Doe"}]
    assert detail_response.status_code == 200
    assert detail_response.json()["data"] == {
        "id": str(parent.id),
        "full_name": "John Doe",
        "email": "john@example.com",
        "city": "London",
    }


@pytest.mark.django_db
def test_search_filters_by_skill_and_rating(client, lsa):
    response = client.get("/api/v1/lsas/search/", {"skill": "autism", "rating": "4.5"})

    assert response.status_code == 200
    assert response.json()["data"] == [
        {
            "id": str(lsa.id),
            "name": "Alice",
            "rating": 4.8,
            "experience": 8,
            "hourly_rate": 60.0,
            "skills": ["Autism", "Speech Therapy"],
        }
    ]


@pytest.mark.django_db
def test_retrieve_active_lsa_profile(client, lsa):
    response = client.get(f"/api/v1/lsas/{lsa.id}/")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "id": str(lsa.id),
        "name": "Alice",
        "bio": "Experienced learning support assistant.",
        "experience": 8,
        "rating": 4.8,
        "hourly_rate": 60.0,
        "skills": ["Autism", "Speech Therapy"],
    }


@pytest.mark.django_db
def test_search_filters_by_available_slot_and_hides_booked_slots(client, lsa):
    available_date = date(2026, 8, 10)
    available = Availability.objects.create(
        lsa=lsa,
        date=available_date,
        start_time=time(9),
        end_time=time(10),
        status=Availability.Status.AVAILABLE,
    )
    Availability.objects.create(
        lsa=lsa,
        date=available_date,
        start_time=time(10),
        end_time=time(11),
        status=Availability.Status.BOOKED,
    )

    search_response = client.get("/api/v1/lsas/search/", {"available_date": "2026-08-10"})
    availability_response = client.get(f"/api/v1/lsas/{lsa.id}/availability/")

    assert search_response.status_code == 200
    assert [item["id"] for item in search_response.json()["data"]] == [str(lsa.id)]
    assert availability_response.status_code == 200
    assert availability_response.json()["data"] == [
        {
            "id": str(available.id),
            "date": "2026-08-10",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
        }
    ]


@pytest.mark.django_db
def test_search_validates_invalid_parameters_and_returns_empty_results(client, lsa):
    invalid_date = client.get("/api/v1/lsas/search/", {"available_date": "not-a-date"})
    negative_experience = client.get("/api/v1/lsas/search/", {"experience": "-1"})
    no_match = client.get("/api/v1/lsas/search/", {"skill": "Unknown skill"})

    assert invalid_date.status_code == 400
    assert negative_experience.status_code == 400
    assert invalid_date.json()["success"] is False
    assert negative_experience.json()["success"] is False
    assert no_match.status_code == 200
    assert no_match.json()["data"] == []
