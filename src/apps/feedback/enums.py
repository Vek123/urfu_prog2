from enum import Enum


class StringEnum(str, Enum):
    def __str__(self):
        return self.value


class Positions(StringEnum):
    DEV = ('DEV', 2.2, False)
    HR = ('HR', 1.2, False)
    TL = ('TL', 2.6, True)
    PO = ('PO', 3.0, True)
    TPM = ('TPM', 3.5, True)
    CTO = ('CTO', 4.0, True)

    def __new__(cls, value, coefficient, is_manager):
        instance = str.__new__(cls, value)
        instance._value_ = value
        instance.coefficient = coefficient
        instance.isManager = is_manager
        return instance


class Codes(StringEnum):
    SUCCESS = 'success'
    FAILED = 'failed'


class ErrorCodes(StringEnum):
    EMPTY = ''
    VALIDATION_EXCEPTION = 'ValidationException'
    UNSUPPORTED_EXCEPTION = 'UnsupportedCodeException'
    UNKNOWN_EXCEPTION = 'UnknownException'
    DOWNSTREAM_EXCEPTION = 'DownstreamServiceException'


class ErrorMessages(StringEnum):
    EMPTY = ''
    VALIDATION = 'Ошибка валидации'
    UNSUPPORTED = 'Не поддерживаемая ошибка'
    UNKNOWN = 'Произошла непредвиденная ошибка'
    DOWNSTREAM = 'Ошибка обращения к Сервису 2'


class Systems(StringEnum):
    ERP = 'ERP'
    CRM = 'CRM'
    WMS = 'WMS'
    SERVICE1 = 'Service 1'

    @property
    def description(self):
        return {
            self.ERP: 'Enterprise Resource Planning',
            self.CRM: 'Customer Relationship Management',
            self.WMS: 'Warehouse Management System',
            self.SERVICE1: 'First REST service',
        }[self]
