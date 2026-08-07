import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q


class LSAProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255, db_index=True)
    bio = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(rating__gte=0) & Q(rating__lte=5),
                name="lsa_rating_between_zero_and_five",
            )
        ]

    def __str__(self):
        return self.full_name


class Skill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LSASkill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lsa = models.ForeignKey(
        LSAProfile,
        on_delete=models.CASCADE,
        related_name="lsa_skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="lsa_skills",
    )
    experience_years = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("lsa", "skill"), name="unique_lsa_skill"),
        ]

    def __str__(self):
        return f"{self.lsa} — {self.skill}"


class Availability(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        BOOKED = "BOOKED", "Booked"
        BLOCKED = "BLOCKED", "Blocked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lsa = models.ForeignKey(
        LSAProfile,
        on_delete=models.CASCADE,
        related_name="availability_slots",
    )
    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
    )

    class Meta:
        ordering = ["date", "start_time"]
        indexes = [models.Index(fields=("lsa", "date"), name="availability_lsa_date_idx")]
        constraints = [
            models.CheckConstraint(
                condition=Q(start_time__lt=F("end_time")),
                name="availability_start_before_end",
            )
        ]

    def __str__(self):
        return f"{self.lsa} — {self.date} {self.start_time}-{self.end_time}"
