from rest_framework import serializers

from .models import Availability, LSAProfile


class LSASearchQuerySerializer(serializers.Serializer):
    skill = serializers.CharField(required=False, allow_blank=False, max_length=150)
    experience = serializers.IntegerField(required=False, min_value=0)
    rating = serializers.DecimalField(required=False, min_value=0, max_value=5, max_digits=3, decimal_places=2)
    available_date = serializers.DateField(required=False)
    hourly_rate_max = serializers.DecimalField(required=False, min_value=0, max_digits=10, decimal_places=2)


class LSASummarySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="full_name")
    experience = serializers.IntegerField(source="experience_years")
    rating = serializers.FloatField()
    hourly_rate = serializers.FloatField()
    skills = serializers.SerializerMethodField()

    class Meta:
        model = LSAProfile
        fields = ("id", "name", "rating", "experience", "hourly_rate", "skills")

    def get_skills(self, instance):
        return [lsa_skill.skill.name for lsa_skill in instance.lsa_skills.all()]


class LSADetailSerializer(LSASummarySerializer):
    class Meta:
        model = LSAProfile
        fields = ("id", "name", "bio", "experience", "rating", "hourly_rate", "skills")


class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = ("id", "date", "start_time", "end_time")


class ScheduleAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = ("id", "date", "start_time", "end_time", "status")
