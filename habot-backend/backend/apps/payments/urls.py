from django.urls import path

from .views import PaymentProcessAPIView, PaymentWebhookAPIView


urlpatterns = [
    path("process/", PaymentProcessAPIView.as_view(), name="payment-process"),
    path("webhook/", PaymentWebhookAPIView.as_view(), name="payment-webhook"),
]
