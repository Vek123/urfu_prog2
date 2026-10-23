import logging

from django.db import DatabaseError

from .services import audit


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        before = request.user if request.user.is_authenticated else None
        response = self.get_response(request)
        if (
            request.path.startswith("/static/")
            or request.path == "/actuator/health"
            or getattr(request, "audit_logged", False)
        ):
            return response
        user = request.user if request.user.is_authenticated else before
        if user is not None or response.status_code >= 400:
            action = (
                "DENIED"
                if response.status_code in (401, 403, 404)
                else ("INVALID_REQUEST" if response.status_code >= 400 else "VIEW")
            )
            try:
                audit(
                    user,
                    action,
                    f"{request.method} {request.path[:250]}; status={response.status_code}",
                )
            except DatabaseError:
                logging.getLogger("apps.music.actions").exception(
                    "Audit database unavailable"
                )
        return response
