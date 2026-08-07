from rest_framework import serializers

from .models import Parent


class ParentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ("id", "full_name")


class ParentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ("id", "full_name", "email", "city")
