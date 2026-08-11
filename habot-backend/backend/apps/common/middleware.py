from contextvars import ContextVar
from uuid import uuid4


REQUEST_ID_HEADER = "X-Request-ID"
_request_id = ContextVar("request_id", default="-")


def get_request_id():
    return _request_id.get()


class RequestIDFilter:
    def filter(self, record):
        record.request_id = get_request_id()
        return True


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid4().hex
        token = _request_id.set(request_id)
        request.request_id = request_id

        try:
            response = self.get_response(request)
            response[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            _request_id.reset(token)
