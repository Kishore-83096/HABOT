from rest_framework import serializers


class PaymentResultSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField()
    result = serializers.ChoiceField(choices=("success", "failed"))
    gateway_reference = serializers.CharField(required=False, allow_blank=False, max_length=255)
