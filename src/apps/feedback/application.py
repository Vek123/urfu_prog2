import logging

from django.conf import settings

from .forwarding import (ForwardRequestService, ModifySourceRequestService,
                         ModifySystemNameRequestService)
from .models import FeedbackRequest
from .serializers import FeedbackRequestSerializer, FeedbackResponseSerializer
from .services import RESPONSE_MODIFIERS, FeedbackService

logger = logging.getLogger(__name__)


class FeedbackApplicationService:
    def __init__(self, feedback_service=None, forwarder=None):
        self.feedback_service = (feedback_service if feedback_service is not None
                                 else FeedbackService(RESPONSE_MODIFIERS[
                                     settings.FEEDBACK_RESPONSE_MODIFIER]()))
        self.forwarder = forwarder
        if self.forwarder is None and settings.FEEDBACK_FORWARD_REQUESTS:
            self.forwarder = ForwardRequestService(
                settings.SERVICE2_URL, settings.SERVICE2_TIMEOUT,
                (ModifySystemNameRequestService(), ModifySourceRequestService()))

    def handle(self, payload, received_at_ns):
        logger.info('Incoming request: %s', payload)
        serializer = FeedbackRequestSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        message = FeedbackRequest(**serializer.validated_data)
        logger.info('Validated request: %s', message)
        result = self.feedback_service.handle(message)
        if self.forwarder is not None:
            self.forwarder.send(message, received_at_ns)
        data = FeedbackResponseSerializer(result).data
        logger.info('uid=%s response status=200 body=%s', message.uid, data)
        return data
