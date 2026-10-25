from threading import Lock
from time import perf_counter

import django
from django.db import DatabaseError, connection
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from .access import role_for

started = perf_counter()
lock = Lock()
count = 0
total = maximum = 0.0


def record_request(elapsed):
    global count, total, maximum
    with lock:
        count += 1
        total += elapsed
        maximum = max(maximum, elapsed)


class AdminPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and role_for(request.user) == "ADMIN"


class HealthView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    http_method_names = ("get", "head", "options")

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except DatabaseError:
            return Response({"status": "DOWN"}, status=503)
        return Response({"status": "UP", "components": {"db": {"status": "UP"}}})


class InfoView(APIView):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (AdminPermission,)
    http_method_names = ("get", "head", "options")

    def get(self, request):
        return Response(
            {
                "app": {
                    "name": "Музыкальный каталог",
                    "version": "1.0.0",
                    "framework": "Django " + django.get_version(),
                    "variant": 10,
                }
            }
        )


class MetricsView(InfoView):
    def get(self, request, metric=None):
        names = ("http.server.requests", "process.uptime")
        if metric is None:
            return Response({"names": names})
        if metric == "process.uptime":
            values = [("VALUE", perf_counter() - started)]
        elif metric == "http.server.requests":
            with lock:
                values = [("COUNT", count), ("TOTAL_TIME", total), ("MAX", maximum)]
        else:
            return Response({"detail": "Метрика не найдена."}, status=404)
        return Response(
            {
                "name": metric,
                "baseUnit": "seconds",
                "measurements": [
                    {"statistic": key, "value": value} for key, value in values
                ],
            }
        )
