from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class FeedbackRequest:
    uid: str
    operationUid: str
    systemTime: str
    communicationId: int
    systemName: str | None = None
    source: str | None = None
    templateId: int = 0
    productCode: int = 0
    smsCode: int = 0


@dataclass(frozen=True)
class FeedbackResponse:
    uid: str
    operationUid: str
    systemTime: str
    code: str = 'success'
    errorCode: str = ''
    errorMessage: str = ''

    @classmethod
    def create(cls, uid='', operation_uid='', *, error_code='', message=''):
        timestamp = datetime.now(UTC).isoformat(timespec='milliseconds')
        return cls(uid, operation_uid, timestamp.replace('+00:00', 'Z'),
                   'failed' if error_code else 'success', error_code, message)
