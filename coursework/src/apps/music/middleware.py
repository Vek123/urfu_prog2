import logging
from time import perf_counter

from django.db import DatabaseError

from .monitoring import record_request
from .services import audit


class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        begin = perf_counter()
        try:
            return self.get_response(request)
        finally:
            record_request(perf_counter() - begin)


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/static/") or request.path == "/actuator/health":
            return self.get_response(request)

        description = f"{request.method} {request.path[:250]}"
        self.log(request, "REQUEST", description)
        response = self.get_response(request)
        if response.status_code >= 400:
            self.log(
                request,
                "RESPONSE",
                f"{description}; status={response.status_code}",
            )
        return response

    def log(self, request, action, description):
        try:
            audit(request.user, action, description)
        except DatabaseError:
            logging.getLogger("apps.music.actions").exception(
                "Audit database unavailable"
            )
