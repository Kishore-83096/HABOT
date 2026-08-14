from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from apps.common.responses import success_response

from .services import bootstrap_test_data, cleanup_test_data


def ensure_test_data_enabled():
    if not getattr(settings, "TEST_DATA_API_ENABLED", False):
        raise PermissionDenied("Test-data endpoints are disabled in this environment.")


class TestDataBootstrapAPIView(APIView):
    @extend_schema(
        tags=["Test Data"],
        summary="Create a disposable Postman test fixture",
        description="Development/testing utility. Creates marked synthetic records for one Postman run.",
    )
    def post(self, request):
        ensure_test_data_enabled()
        data = bootstrap_test_data(request.data.get("test_run_id"))
        return success_response(data, message="Test data bootstrap completed.", status=status.HTTP_201_CREATED)


class TestDataCleanupAPIView(APIView):
    @extend_schema(
        tags=["Test Data"],
        summary="Delete a disposable Postman test fixture",
        description="Development/testing utility. Deletes only records marked for the supplied Postman test run.",
    )
    def delete(self, request, test_run_id):
        ensure_test_data_enabled()
        data = cleanup_test_data(test_run_id)
        return success_response(data, message="Test data cleanup completed.")
