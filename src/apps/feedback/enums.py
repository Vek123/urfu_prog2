from enum import Enum


class StringEnum(str, Enum):
    def __str__(self):
        return self.value


class Codes(StringEnum):
    SUCCESS = 'success'
    FAILED = 'failed'


class ErrorCodes(StringEnum):
    EMPTY = ''
    VALIDATION_EXCEPTION = 'ValidationException'
    UNSUPPORTED_EXCEPTION = 'UnsupportedCodeException'
    UNKNOWN_EXCEPTION = 'UnknownException'


class ErrorMessages(StringEnum):
    EMPTY = ''
    VALIDATION = 'Ошибка валидации'
    UNSUPPORTED = 'Не поддерживаемая ошибка'
    UNKNOWN = 'Произошла непредвиденная ошибка'


class Systems(StringEnum):
    ERP = 'ERP'
    CRM = 'CRM'
    WMS = 'WMS'

    @property
    def description(self):
        return {
            self.ERP: 'Enterprise Resource Planning',
            self.CRM: 'Customer Relationship Management',
            self.WMS: 'Warehouse Management System',
        }[self]
