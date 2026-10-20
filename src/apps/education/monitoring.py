from platform import python_version
from threading import Lock
from time import perf_counter

import django
from django.db import connection, DatabaseError
from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView


class RequestMetrics:
    def __init__(self):
        self.started = perf_counter()
        self.started_at = timezone.now()
        self.lock = Lock()
        self.count = 0
        self.total_time = 0.0
        self.max_time = 0.0

    def record(self, elapsed):
        with self.lock:
            self.count += 1
            self.total_time += elapsed
            self.max_time = max(self.max_time, elapsed)

    def measurements(self):
        with self.lock:
            return [{'statistic': 'COUNT', 'value': self.count},
                    {'statistic': 'TOTAL_TIME', 'value': self.total_time},
                    {'statistic': 'MAX', 'value': self.max_time}]


request_metrics = RequestMetrics()


class RequestMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = perf_counter()
        try:
            return self.get_response(request)
        finally:
            request_metrics.record(perf_counter() - started)


class DiagnosticView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    renderer_classes = (JSONRenderer,)
    http_method_names = ('get', 'head', 'options')


class ActuatorIndexView(DiagnosticView):
    def get(self, request):
        return Response({'_links': {
            name: {'href': request.build_absolute_uri(path), 'templated': False}
            for name, path in (('self', '/actuator'), ('health', '/actuator/health'),
                               ('info', '/actuator/info'), ('metrics', '/actuator/metrics'))
        }})


class HealthView(DiagnosticView):
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                cursor.fetchone()
        except DatabaseError:
            return Response({'status': 'DOWN', 'components': {'db': {'status': 'DOWN'}}}, status=503)
        return Response({'status': 'UP', 'components': {
            'db': {'status': 'UP', 'details': {'database': connection.vendor}}}})


class InfoView(DiagnosticView):
    def get(self, request):
        return Response({'app': {'name': 'Учебные справочники', 'version': '1.0.0',
                                  'framework': 'Django ' + django.get_version(),
                                  'python': python_version()},
                         'startedAt': request_metrics.started_at.isoformat()})


class MetricsView(DiagnosticView):
    def get(self, request, metric_name=None):
        if metric_name is None:
            return Response({'names': ['http.server.requests', 'process.uptime']})
        if metric_name == 'http.server.requests':
            return Response({'name': metric_name,
                             'description': 'Завершённые HTTP-запросы текущего процесса',
                             'baseUnit': 'seconds',
                             'measurements': request_metrics.measurements(), 'availableTags': []})
        if metric_name == 'process.uptime':
            return Response({'name': metric_name, 'description': 'Время работы текущего процесса',
                             'baseUnit': 'seconds', 'measurements': [
                                 {'statistic': 'VALUE', 'value': perf_counter() - request_metrics.started}],
                             'availableTags': []})
        raise NotFound('Метрика не найдена.')
