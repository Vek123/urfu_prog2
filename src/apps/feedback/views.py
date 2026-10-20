import logging

from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler

from .enums import ErrorCodes, ErrorMessages
from .exceptions import UnsupportedCodeException
from .models import FeedbackRequest, FeedbackResponse
from .serializers import FeedbackRequestSerializer, FeedbackResponseSerializer
from .services import RESPONSE_MODIFIERS, FeedbackService

logger = logging.getLogger(__name__)


def feedback_exception_handler(error, context):
    response = exception_handler(error, context)
    details = ''
    if isinstance(error, UnsupportedCodeException):
        error_code = ErrorCodes.UNSUPPORTED_EXCEPTION
        message = ErrorMessages.UNSUPPORTED
    elif response is not None:
        error_code = ErrorCodes.VALIDATION_EXCEPTION
        if isinstance(error, ValidationError) and isinstance(error.detail, dict):
            details = '; '.join(
                f'{field}: {", ".join(map(str, messages))}'
                for field, messages in error.detail.items())
        else:
            details = str(error.detail)
        message = ErrorMessages.VALIDATION
        logger.error('Request rejected: %s: %s', type(error).__name__, details)
    else:
        logger.exception('Unexpected feedback processing error')
        error_code = ErrorCodes.UNKNOWN_EXCEPTION
        message = ErrorMessages.UNKNOWN

    payload = getattr(context['view'], 'payload', None)
    payload = payload if isinstance(payload, dict) else {}
    identifiers = [payload.get(field, '') for field in ('uid', 'operationUid')]
    identifiers = [value if isinstance(value, str) else '' for value in identifiers]
    result = FeedbackResponse.create(*identifiers, error_code=error_code,
                                     message=message, details=details)
    status_code = response.status_code if response is not None else 500
    data = FeedbackResponseSerializer(result).data
    logger.info('uid=%s error response status=%s body=%s',
                identifiers[0], status_code, data)
    return Response(data, status=status_code,
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
        logger.info('Request received: %s %s', request.method, request.path)
        self.payload = request.data
        logger.info('Incoming request: %s', self.payload)
        serializer = FeedbackRequestSerializer(data=self.payload)
        serializer.is_valid(raise_exception=True)
        message = FeedbackRequest(**serializer.validated_data)
        logger.info('Validated request: %s', message)
        modifier = RESPONSE_MODIFIERS[settings.FEEDBACK_RESPONSE_MODIFIER]()
        result = FeedbackService(modifier).handle(message)
        data = FeedbackResponseSerializer(result).data
        logger.info('uid=%s response status=200 body=%s', message.uid, data)
        return Response(data)
