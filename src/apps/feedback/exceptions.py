from rest_framework.exceptions import APIException

from .enums import ErrorCodes, ErrorMessages


class UnsupportedCodeException(APIException):
    status_code = 400
    default_detail = ErrorMessages.UNSUPPORTED.value
    default_code = ErrorCodes.UNSUPPORTED_EXCEPTION.value
