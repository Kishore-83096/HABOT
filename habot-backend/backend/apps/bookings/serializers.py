from rest_framework import serializers

from apps.parents.serializers import ParentDetailSerializer
from apps.lsas.models import Availability

from .models import Booking


class BookingCreateSerializer(serializers.Serializer):
    parent_id = serializers.UUIDField()
    availability_id = serializers.UUIDField()


class BookingAvailabilitySerializer(serializers.ModelSerializer):
    lsa_id = serializers.UUIDField(read_only=True)
    lsa_name = serializers.CharField(source="lsa.full_name", read_only=True)

    class Meta:
        model = Availability
        fields = ("id", "lsa_id", "lsa_name", "date", "start_time", "end_time", "status")


class BookingDetailSerializer(serializers.ModelSerializer):
    parent = ParentDetailSerializer(read_only=True)
    availability = BookingAvailabilitySerializer(read_only=True)
    payment_status = serializers.SerializerMethodField()
    booking_id = serializers.UUIDField(source="id", read_only=True)
    booking_status = serializers.CharField(source="status", read_only=True)
    lsa = serializers.SerializerMethodField()
    slot = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            "id",
            "booking_id",
            "parent",
            "lsa",
            "slot",
            "availability",
            "status",
            "booking_status",
            "payment_status",
            "created_at",
            "updated_at",
        )

    def get_payment_status(self, instance):
        payments = getattr(instance, "prefetched_payments", ())
        return payments[0].status if payments else None

    def get_lsa(self, instance):
        return {"id": str(instance.availability.lsa_id), "name": instance.availability.lsa.full_name}

    def get_slot(self, instance):
        availability = instance.availability
        return {"date": availability.date, "start_time": availability.start_time, "end_time": availability.end_time}
