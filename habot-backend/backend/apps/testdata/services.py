import re
import uuid
from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.bookings.models import Booking
from apps.lsas.models import Availability, LSAProfile, LSASkill, Skill
from apps.parents.models import Parent
from apps.payments.models import Payment


TEST_RUN_PREFIX = "POSTMAN_TEST_"
TEST_RUN_RE = re.compile(r"^POSTMAN_TEST_[A-Za-z0-9_-]{8,80}$")


def normalize_test_run_id(test_run_id=None):
    if not test_run_id:
        return f"{TEST_RUN_PREFIX}{uuid.uuid4().hex}"
    if not TEST_RUN_RE.fullmatch(test_run_id):
        raise ValidationError({"test_run_id": "Use a POSTMAN_TEST_ run id containing only letters, numbers, _ or -."})
    return test_run_id


def marker(test_run_id, label):
    return f"{TEST_RUN_PREFIX}{label}_{test_run_id}"


def object_belongs_to_run(value, test_run_id):
    return bool(value and test_run_id in value and value.startswith(TEST_RUN_PREFIX))


@transaction.atomic
def bootstrap_test_data(test_run_id=None):
    test_run_id = normalize_test_run_id(test_run_id)
    User = get_user_model()

    admin = User.objects.create_user(
        username=marker(test_run_id, "ADMIN")[:150],
        email=f"postman_admin_{test_run_id.lower()}@example.test"[:254],
        password=uuid.uuid4().hex,
        is_staff=True,
        is_superuser=False,
    )
    parent = Parent.objects.create(
        full_name=marker(test_run_id, "PARENT"),
        email=f"postman_parent_{test_run_id.lower()}@example.test"[:254],
        phone="9999999999",
        city="Postman City",
    )
    lsa = LSAProfile.objects.create(
        full_name=marker(test_run_id, "LSA"),
        bio=f"Synthetic LSA fixture for {test_run_id}.",
        experience_years=7,
        hourly_rate=Decimal("750.00"),
        rating=Decimal("4.80"),
        is_active=True,
    )
    skill = Skill.objects.create(
        name=marker(test_run_id, "SKILL_MATH"),
        category="Postman Test",
        description=f"Synthetic skill fixture for {test_run_id}.",
    )
    lsa_skill = LSASkill.objects.create(lsa=lsa, skill=skill, experience_years=7)

    first_date = timezone.localdate() + timedelta(days=7)
    availability = [
        Availability.objects.create(lsa=lsa, date=first_date, start_time=time(9, 0), end_time=time(10, 0)),
        Availability.objects.create(
            lsa=lsa,
            date=first_date + timedelta(days=1),
            start_time=time(11, 0),
            end_time=time(12, 0),
        ),
    ]

    return {
        "test_run_id": test_run_id,
        "admin": {"id": str(admin.id), "username": admin.username, "is_staff": admin.is_staff},
        "parent": {"id": str(parent.id), "full_name": parent.full_name, "email": parent.email},
        "lsa": {"id": str(lsa.id), "name": lsa.full_name},
        "skills": [{"id": str(skill.id), "name": skill.name, "category": skill.category}],
        "lsa_skills": [{"id": str(lsa_skill.id), "lsa_id": str(lsa.id), "skill_id": str(skill.id)}],
        "availability": [
            {
                "id": str(slot.id),
                "date": slot.date.isoformat(),
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "status": slot.status,
            }
            for slot in availability
        ],
    }


@transaction.atomic
def cleanup_test_data(test_run_id):
    test_run_id = normalize_test_run_id(test_run_id)
    User = get_user_model()

    parents = Parent.objects.filter(full_name=marker(test_run_id, "PARENT"), email__contains=test_run_id.lower())
    lsas = LSAProfile.objects.filter(full_name=marker(test_run_id, "LSA"))
    skills = Skill.objects.filter(name__startswith=f"{TEST_RUN_PREFIX}SKILL_", name__contains=test_run_id)
    admins = User.objects.filter(username=marker(test_run_id, "ADMIN")[:150], email__contains=test_run_id.lower())

    for parent in parents:
        if not object_belongs_to_run(parent.full_name, test_run_id):
            raise ValidationError({"test_run_id": "Parent marker did not match this test run."})
    for lsa in lsas:
        if not object_belongs_to_run(lsa.full_name, test_run_id):
            raise ValidationError({"test_run_id": "LSA marker did not match this test run."})
    for skill in skills:
        if not object_belongs_to_run(skill.name, test_run_id):
            raise ValidationError({"test_run_id": "Skill marker did not match this test run."})

    bookings = Booking.objects.filter(parent__in=parents) | Booking.objects.filter(availability__lsa__in=lsas)
    payment_count, _ = Payment.objects.filter(booking__in=bookings).delete()
    booking_count, _ = bookings.distinct().delete()
    availability_count, _ = Availability.objects.filter(lsa__in=lsas).delete()
    lsa_skill_count, _ = LSASkill.objects.filter(lsa__in=lsas).delete()
    lsa_count, _ = lsas.delete()
    parent_count, _ = parents.delete()
    skill_count, _ = skills.delete()
    admin_count, _ = admins.delete()

    return {
        "test_run_id": test_run_id,
        "deleted": {
            "payments": payment_count,
            "bookings": booking_count,
            "availability": availability_count,
            "lsa_skills": lsa_skill_count,
            "lsas": lsa_count,
            "parents": parent_count,
            "skills": skill_count,
            "admins": admin_count,
        },
    }
