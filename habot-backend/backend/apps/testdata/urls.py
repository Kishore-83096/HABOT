from django.urls import path

from .views import TestDataBootstrapAPIView, TestDataCleanupAPIView


urlpatterns = [
    path("bootstrap/", TestDataBootstrapAPIView.as_view(), name="test-data-bootstrap"),
    path("cleanup/<str:test_run_id>/", TestDataCleanupAPIView.as_view(), name="test-data-cleanup"),
]
