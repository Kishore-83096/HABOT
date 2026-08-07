import logging

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from django.db import connection

logger = logging.getLogger(__name__)
from django.http import JsonResponse
from django.urls import path


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logger.exception("Health check database probe failed")
        return JsonResponse(
            {"status": "unhealthy", "database": "unavailable"},
            status=503,
        )

    return JsonResponse({"status": "ok", "database": "connected"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
]
