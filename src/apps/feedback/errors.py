import logging

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .enums import ErrorCodes, ErrorMessages
from .exceptions import DownstreamServiceException, UnsupportedCodeException
from .models import FeedbackResponse
from .serializers import FeedbackResponseSerializer

logger = logging.getLogger(__name__)


def feedback_exception_handler(error, context):
    response = exception_handler(error, context)
    details = ''
    if isinstance(error, UnsupportedCodeException):
        error_code = ErrorCodes.UNSUPPORTED_EXCEPTION
        message = ErrorMessages.UNSUPPORTED
    elif isinstance(error, DownstreamServiceException):
        error_code = ErrorCodes.DOWNSTREAM_EXCEPTION
        message = ErrorMessages.DOWNSTREAM
        details = str(error.detail)
        logger.error('Forwarding failed: %s', details)
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

