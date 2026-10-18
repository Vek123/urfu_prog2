from .exceptions import UnsupportedCodeException
from .models import FeedbackResponse


class FeedbackService:
    def handle(self, message):
        if message.uid == '123':
            raise UnsupportedCodeException()
        return FeedbackResponse.create(message.uid, message.operationUid)
