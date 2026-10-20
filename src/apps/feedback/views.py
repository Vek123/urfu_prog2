import logging
from time import time_ns

from django.conf import settings
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from .application import FeedbackApplicationService
from .errors import feedback_exception_handler
from .timing import log_delivery_timing

logger = logging.getLogger(__name__)


class FeedbackView(APIView):
    parser_classes = (JSONParser,)
    renderer_classes = (JSONRenderer,)
    authentication_classes = ()
    permission_classes = (AllowAny,)
    http_method_names = ('post', 'options')

    def dispatch(self, request, *args, **kwargs):
        self.received_at_ns = time_ns()
        return super().dispatch(request, *args, **kwargs)

    def get_exception_handler(self):
        return feedback_exception_handler

    def post(self, request, *args, **kwargs):
        logger.info('Request received: %s %s', request.method, request.path)
        self.payload = request.data
        if not settings.FEEDBACK_FORWARD_REQUESTS:
            log_delivery_timing(request, self.received_at_ns)
        result = FeedbackApplicationService().handle(self.payload, self.received_at_ns)
        return Response(result)
