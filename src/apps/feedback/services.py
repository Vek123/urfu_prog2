import logging
from abc import ABC, abstractmethod
from dataclasses import replace
from uuid import uuid4

from rest_framework.exceptions import ValidationError

from .bonuses import AnnualBonusServiceImpl, QuarterlyBonusServiceImpl
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
    def __init__(self, response_modifier: ModifyResponseService,
                 annual_service=None, quarterly_service=None):
        self.response_modifier = response_modifier
        self.annual_service = (annual_service if annual_service is not None
                               else AnnualBonusServiceImpl())
        self.quarterly_service = (quarterly_service if quarterly_service is not None
                                  else QuarterlyBonusServiceImpl(self.annual_service))

    def handle(self, message):
        logger.info('uid=%s business processing started', message.uid)
        if message.uid == '123':
            logger.error('uid=%s UnsupportedCodeException: %s',
                         message.uid, UnsupportedCodeException.default_detail)
            raise UnsupportedCodeException()
        response = FeedbackResponse.create(message.uid, message.operationUid)
        try:
            annual = self.annual_service.calculate(
                message.position, message.salary, message.bonus,
                message.workDays, message.year)
            quarterly = (self.quarterly_service.calculate(
                message.position, message.salary, message.bonus,
                message.workDays, message.year) if message.position.isManager else None)
        except ValueError as error:
            raise ValidationError({'annualBonus': [str(error)]}) from error
        response = replace(response, annualBonus=annual, quarterlyBonus=quarterly)
        logger.info('uid=%s bonus calculated position=%s year=%s annual=%s quarterly=%s',
                    message.uid, message.position, message.year, annual, quarterly)
        logger.info('uid=%s response created: %s', message.uid, response)
        return self.response_modifier.modify(response)
