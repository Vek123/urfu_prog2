import json
from dataclasses import asdict, dataclass, field

from .enums import Codes, ErrorCodes, ErrorMessages, Systems
from .util import DateTimeUtil


@dataclass(frozen=True)
class FeedbackRequest:
    # Идентификатор сообщения из запроса.
    uid: str
    # Идентификатор операции.
    operationUid: str
    # Время формирования ответа сервером в UTC.
    systemTime: str
    # Уникальный идентификатор коммуникации, от 1 до 100000.
    communicationId: int
    # Имя системы отправителя.
    systemName: Systems | None = None
    # Наименование ресурса, отправившего сообщение.
    source: str | None = None
    # Уникальный идентификатор шаблона.
    templateId: int = 0
    # Код продукта.
    productCode: int = 0
    # Код СМС.
    smsCode: int = 0

    def __str__(self):
        return json.dumps(asdict(self), ensure_ascii=False)


@dataclass(frozen=True)
class FeedbackResponse:
    # Идентификатор сообщения из запроса.
    uid: str
    # Идентификатор операции.
    operationUid: str
    # Время формирования ответа сервером в UTC.
    systemTime: str
    # Результат обработки: success или failed.
    code: Codes = Codes.SUCCESS
    # Код ошибки; при успехе пустая строка.
    errorCode: ErrorCodes = ErrorCodes.EMPTY
    # Базовое описание ошибки; при успехе пустая строка.
    errorMessage: ErrorMessages = ErrorMessages.EMPTY
    # Внутренние подробности для errorMessage, отдельно в JSON не передаются.
    errorDetails: str = field(default='', repr=False)

    @classmethod
    def create(cls, uid='', operation_uid='', *, error_code=ErrorCodes.EMPTY,
               message=ErrorMessages.EMPTY, details=''):
        return cls(uid, operation_uid, DateTimeUtil.format_utc(),
                   Codes.FAILED if error_code else Codes.SUCCESS,
                   error_code, message, details)
