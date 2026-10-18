from rest_framework.exceptions import APIException


class UnsupportedCodeException(APIException):
    status_code = 400
    default_detail = 'Не поддерживаемая ошибка'
    default_code = 'UnsupportedCodeException'
