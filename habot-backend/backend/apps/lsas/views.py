from django.db.models import Count, Prefetch, Q
from rest_framework import generics

from .models import Availability, LSASkill, LSAProfile
from .serializers import (
    AvailabilitySerializer,
    LSADetailSerializer,
    LSASearchQuerySerializer,
    LSASummarySerializer,
    ScheduleAvailabilitySerializer,
)


def lsa_queryset():
    """Load each LSA's skills in a fixed number of queries."""
    skills = LSASkill.objects.select_related("skill").order_by("skill__name")
    return LSAProfile.objects.prefetch_related(Prefetch("lsa_skills", queryset=skills))


class LSASearchAPIView(generics.ListAPIView):
    serializer_class = LSASummarySerializer
    pagination_class = None

    def get_queryset(self):
        query_serializer = LSASearchQuerySerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        filters = query_serializer.validated_data

        queryset = lsa_queryset().filter(is_active=True).annotate(
            skill_count=Count("lsa_skills", distinct=True)
        )
        conditions = Q()
        if skill := filters.get("skill"):
            conditions &= Q(lsa_skills__skill__name__iexact=skill)
        if (experience := filters.get("experience")) is not None:
            conditions &= Q(experience_years__gte=experience)
        if (rating := filters.get("rating")) is not None:
            conditions &= Q(rating__gte=rating)
        if (hourly_rate_max := filters.get("hourly_rate_max")) is not None:
            conditions &= Q(hourly_rate__lte=hourly_rate_max)
        if (available_date := filters.get("available_date")) is not None:
            conditions &= Q(
                availability_slots__date=available_date,
                availability_slots__status=Availability.Status.AVAILABLE,
            )

        return queryset.filter(conditions).distinct()


class LSADetailAPIView(generics.RetrieveAPIView):
    serializer_class = LSADetailSerializer

    def get_queryset(self):
        return lsa_queryset().filter(is_active=True)


class AvailabilityAPIView(generics.ListAPIView):
    serializer_class = AvailabilitySerializer
    pagination_class = None

    def get_queryset(self):
        # select_related keeps this endpoint efficient if its serializer grows to expose LSA data.
        return Availability.objects.select_related("lsa").filter(
            lsa_id=self.kwargs["pk"],
            lsa__is_active=True,
            status=Availability.Status.AVAILABLE,
        )


class LSAScheduleAPIView(generics.ListAPIView):
    serializer_class = ScheduleAvailabilitySerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Availability.objects.select_related("lsa").filter(lsa_id=self.kwargs["pk"])
        if date := self.request.query_params.get("date"):
            # Let Django's query parsing return its standard 400 for invalid dates.
            from rest_framework.exceptions import ValidationError
            from datetime import date as date_type
            try:
                date_type.fromisoformat(date)
            except ValueError as exc:
                raise ValidationError({"date": "Use ISO-8601 date format (YYYY-MM-DD)."}) from exc
            queryset = queryset.filter(date=date)
        return queryset
