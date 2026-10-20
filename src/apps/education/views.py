import logging

from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler

from .services import DisciplineService, StudentService

logger = logging.getLogger(__name__)


def success(data, message, status=200):
    return Response({'success': True, 'message': message,
                     'data': data, 'errors': None}, status=status)


def education_exception_handler(error, context):
    response = exception_handler(error, context)
    if response is None:
        logger.exception('Ошибка обработки учебных данных')
        return Response({'success': False, 'message': 'Внутренняя ошибка сервера.',
                         'data': None, 'errors': None}, status=500)
    details = response.data
    message = 'Ошибка проверки данных.'
    if isinstance(details, dict) and 'detail' in details:
        message = str(details['detail'])
    response.data = {'success': False, 'message': message,
                     'data': None, 'errors': details}
    return response


class ResourceView(APIView):
    parser_classes = (JSONParser,)
    renderer_classes = (JSONRenderer,)
    authentication_classes = ()
    permission_classes = (AllowAny,)
    service_class = None

    def get_exception_handler(self):
        return education_exception_handler


class CollectionView(ResourceView):
    http_method_names = ('get', 'post', 'put', 'head', 'options')

    def get(self, request):
        return success(self.service_class().get_all(), 'Список получен.')

    def post(self, request):
        return success(self.service_class().create(request.data), 'Запись создана.', 201)

    def put(self, request):
        return success(self.service_class().update(request.data), 'Запись изменена.')


class DetailView(ResourceView):
    http_method_names = ('get', 'delete', 'head', 'options')

    def get(self, request, item_id):
        return success(self.service_class().get_by_id(item_id), 'Запись получена.')

    def delete(self, request, item_id):
        return success(self.service_class().delete(item_id), 'Запись удалена.')


class StudentCollectionView(CollectionView):
    service_class = StudentService


class StudentDetailView(DetailView):
    service_class = StudentService


class DisciplineCollectionView(CollectionView):
    service_class = DisciplineService


class DisciplineDetailView(DetailView):
    service_class = DisciplineService
