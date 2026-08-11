from rest_framework import serializers


class PaymentResultSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField()
    result = serializers.ChoiceField(choices=("success", "failed"))
    gateway_reference = serializers.CharField(required=False, allow_blank=False, max_length=255)


class MockPaymentGatewaySerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()
    booking_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.ChoiceField(choices=("INR",))
    result = serializers.ChoiceField(choices=("success", "failed"))
