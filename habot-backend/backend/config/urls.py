import logging

from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.common.responses import error_payload, success_payload

logger = logging.getLogger(__name__)


def live_check(request):
    return JsonResponse(success_payload({"status": "ok"}, message="Application is live."))


def ready_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logger.exception("Health check database probe failed")
        return JsonResponse(
            error_payload(
                message="Application is not ready.",
                errors={"database": "unavailable"},
            ),
            status=503,
        )

    return JsonResponse(
        success_payload(
            {"status": "ok", "database": "connected"},
            message="Application is ready.",
        )
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", ready_check, name="health-check"),
    path("health/live/", live_check, name="health-live"),
    path("health/ready/", ready_check, name="health-ready"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/parents/", include("apps.parents.urls")),
    path("api/v1/lsas/", include("apps.lsas.urls")),
    path("api/v1/bookings/", include("apps.bookings.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("mock-payment-gateway/", include("apps.payments.mock_gateway_urls")),
]
