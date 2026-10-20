import logging
from abc import ABC, abstractmethod
from dataclasses import replace
from uuid import uuid4

from .exceptions import UnsupportedCodeException
from .models import FeedbackResponse
from .util import DateTimeUtil

logger = logging.getLogger(__name__)


class ModifyResponseService(ABC):
    @abstractmethod
    def modify(self, response: FeedbackResponse) -> FeedbackResponse:
        raise NotImplementedError


class ModifyOperationUidResponseService(ModifyResponseService):
    def modify(self, response):
        modified = replace(response, operationUid=str(uuid4()))
        logger.info('uid=%s operationUid changed: %s -> %s',
                    response.uid, response.operationUid, modified.operationUid)
        return modified


class ModifySystemTimeResponseService(ModifyResponseService):
    def modify(self, response):
        modified = replace(response, systemTime=DateTimeUtil.format_utc())
        logger.info('uid=%s systemTime updated: %s -> %s',
                    response.uid, response.systemTime, modified.systemTime)
        return modified


RESPONSE_MODIFIERS = {
    'systemTime': ModifySystemTimeResponseService,
    'operationUid': ModifyOperationUidResponseService,
}


class FeedbackService:
    def __init__(self, response_modifier: ModifyResponseService):
        self.response_modifier = response_modifier

    def handle(self, message):
        logger.info('uid=%s business processing started', message.uid)
        if message.uid == '123':
            logger.error('uid=%s UnsupportedCodeException: %s',
                         message.uid, UnsupportedCodeException.default_detail)
            raise UnsupportedCodeException()
        response = FeedbackResponse.create(message.uid, message.operationUid)
        logger.info('uid=%s response created: %s', message.uid, response)
        return self.response_modifier.modify(response)
