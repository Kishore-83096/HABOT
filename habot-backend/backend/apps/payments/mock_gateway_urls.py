from django.urls import path

from .views import MockPaymentGatewayAPIView

urlpatterns = [
    path("payments/", MockPaymentGatewayAPIView.as_view(), name="mock-payment-gateway"),
]
