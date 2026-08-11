from collections.abc import Mapping, Sequence

from rest_framework.response import Response


DEFAULT_SUCCESS_MESSAGE = "Request completed successfully."
DEFAULT_ERROR_MESSAGE = "An error occurred."


def success_payload(data=None, message=DEFAULT_SUCCESS_MESSAGE):
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def error_payload(message=DEFAULT_ERROR_MESSAGE, errors=None):
    return {
        "success": False,
        "message": message,
        "errors": errors,
    }


def success_response(data=None, message=DEFAULT_SUCCESS_MESSAGE, status=200):
    return Response(success_payload(data=data, message=message), status=status)


def error_response(message=DEFAULT_ERROR_MESSAGE, errors=None, status=400):
    return Response(error_payload(message=message, errors=errors), status=status)


def first_error_message(errors):
    if errors is None:
        return DEFAULT_ERROR_MESSAGE
    if isinstance(errors, Mapping):
        for value in errors.values():
            return first_error_message(value)
        return DEFAULT_ERROR_MESSAGE
    if isinstance(errors, str):
        return errors
    if isinstance(errors, Sequence):
        if not errors:
            return DEFAULT_ERROR_MESSAGE
        return first_error_message(errors[0])
    return str(errors)


class EnvelopedListMixin:
    success_message = DEFAULT_SUCCESS_MESSAGE

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data, message=self.success_message)


class EnvelopedRetrieveMixin:
    success_message = DEFAULT_SUCCESS_MESSAGE

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(serializer.data, message=self.success_message)
