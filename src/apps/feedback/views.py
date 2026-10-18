import logging

from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler

from .exceptions import UnsupportedCodeException
from .models import FeedbackRequest, FeedbackResponse
from .serializers import FeedbackRequestSerializer, FeedbackResponseSerializer
from .services import FeedbackService

logger = logging.getLogger(__name__)


def feedback_exception_handler(error, context):
    response = exception_handler(error, context)
    if isinstance(error, UnsupportedCodeException):
        error_code = 'UnsupportedCodeException'
        message = str(error.detail)
    elif response is not None:
        error_code = 'ValidationException'
        if isinstance(error, ValidationError) and isinstance(error.detail, dict):
            details = '; '.join(
                f'{field}: {", ".join(map(str, messages))}'
                for field, messages in error.detail.items())
        else:
            details = str(error.detail)
        message = f'Ошибка валидации: {details}'
    else:
        logger.exception('Unexpected feedback processing error')
        error_code = 'UnknownException'
        message = 'Произошла непредвиденная ошибка'

    payload = getattr(context['view'], 'payload', None)
    payload = payload if isinstance(payload, dict) else {}
    identifiers = [payload.get(field, '') for field in ('uid', 'operationUid')]
    identifiers = [value if isinstance(value, str) else '' for value in identifiers]
    result = FeedbackResponse.create(*identifiers, error_code=error_code, message=message)
    return Response(FeedbackResponseSerializer(result).data,
                    status=response.status_code if response is not None else 500,
                    headers=response.headers if response is not None else None)


class FeedbackView(APIView):
    parser_classes = (JSONParser,)
    renderer_classes = (JSONRenderer,)
    # Public lab API without session/cookie authentication.
    authentication_classes = ()
    permission_classes = (AllowAny,)
    http_method_names = ('post', 'options')

    def get_exception_handler(self):
        return feedback_exception_handler

    def post(self, request, *args, **kwargs):
        self.payload = request.data
        serializer = FeedbackRequestSerializer(data=self.payload)
        serializer.is_valid(raise_exception=True)
        message = FeedbackRequest(**serializer.validated_data)
        result = FeedbackService().handle(message)
        return Response(FeedbackResponseSerializer(result).data)
