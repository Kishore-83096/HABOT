import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.views import exception_handler

from .middleware import get_request_id
from .responses import error_response, first_error_message

logger = logging.getLogger("apps.common")


def custom_exception_handler(exc, context):
    request = context.get("request")
    request_id = (
        getattr(request, "request_id", get_request_id())
        if request
        else get_request_id()
    )

    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = exceptions.PermissionDenied()

    response = exception_handler(exc, context)

    if response is None:
        logger.exception("Unexpected API exception request_id=%s", request_id, exc_info=exc)
        return error_response(
            message="An unexpected error occurred.",
            errors=None,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    detail = response.data
    if isinstance(exc, exceptions.ValidationError):
        errors = detail
        message = first_error_message(errors)
    elif isinstance(detail, dict) and "detail" in detail:
        errors = detail
        message = str(detail["detail"])
    else:
        errors = detail
        message = first_error_message(errors)

    return error_response(message=message, errors=errors, status=response.status_code)
