import json
from dataclasses import asdict, dataclass, field

from .enums import Codes, ErrorCodes, ErrorMessages, Systems
from .util import DateTimeUtil


@dataclass(frozen=True)
class FeedbackRequest:
    uid: str
    operationUid: str
    systemTime: str
    communicationId: int
    systemName: Systems | None = None
    source: str | None = None
    templateId: int = 0
    productCode: int = 0
    smsCode: int = 0

    def __str__(self):
        return json.dumps(asdict(self), ensure_ascii=False)


@dataclass(frozen=True)
class FeedbackResponse:
    uid: str
    operationUid: str
    systemTime: str
    code: Codes = Codes.SUCCESS
    errorCode: ErrorCodes = ErrorCodes.EMPTY
    errorMessage: ErrorMessages = ErrorMessages.EMPTY
    errorDetails: str = field(default='', repr=False)

    @classmethod
    def create(cls, uid='', operation_uid='', *, error_code=ErrorCodes.EMPTY,
               message=ErrorMessages.EMPTY, details=''):
        return cls(uid, operation_uid, DateTimeUtil.format_utc(),
                   Codes.FAILED if error_code else Codes.SUCCESS,
                   error_code, message, details)
