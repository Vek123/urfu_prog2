import json
import logging
import socket
from abc import ABC, abstractmethod
from dataclasses import asdict, replace
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .enums import Systems
from .exceptions import DownstreamServiceException, DownstreamTimeoutException
from .models import FeedbackRequest
from .timing import RECEIVED_AT_HEADER

logger = logging.getLogger(__name__)


class ModifyRequestService(ABC):
    @abstractmethod
    def modify(self, message: FeedbackRequest) -> FeedbackRequest:
        raise NotImplementedError


class ModifySystemNameRequestService(ModifyRequestService):
    def modify(self, message):
        modified = replace(message, systemName=Systems.SERVICE1)
        logger.info('uid=%s request systemName changed: %s -> %s',
                    message.uid, message.systemName, modified.systemName)
        return modified


class ModifySourceRequestService(ModifyRequestService):
    def modify(self, message):
        modified = replace(message, source='Service 1')
        logger.info('uid=%s request source changed: %s -> %s',
                    message.uid, message.source, modified.source)
        return modified


class ForwardRequestService:
    def __init__(self, url, timeout, modifiers):
        self.url = url
        self.timeout = timeout
        self.modifiers = modifiers

    def send(self, message, received_at_ns):
        for modifier in self.modifiers:
            message = modifier.modify(message)
        data = json.dumps(asdict(message), ensure_ascii=False).encode('utf-8')
        outgoing = Request(
            self.url, data=data, method='POST',
            headers={'Content-Type': 'application/json',
                     RECEIVED_AT_HEADER: str(received_at_ns)})
        logger.info('uid=%s forwarding request url=%s body=%s',
                    message.uid, self.url, message)
        try:
            with urlopen(outgoing, timeout=self.timeout) as reply:
                body = json.load(reply)
                if (reply.status != 200 or not isinstance(body, dict)
                        or body.get('code') != 'success'):
                    raise DownstreamServiceException('Некорректный ответ Сервиса 2')
                logger.info('uid=%s Service 2 accepted request status=%s',
                            message.uid, reply.status)
        except HTTPError as error:
            logger.error('uid=%s Service 2 HTTP error status=%s',
                         message.uid, error.code)
            error.close()
            raise DownstreamServiceException(
                f'Сервис 2 вернул HTTP {error.code}') from error
        except (TimeoutError, socket.timeout) as error:
            logger.error('uid=%s Service 2 timeout', message.uid)
            raise DownstreamTimeoutException('Превышено время ожидания Сервиса 2') from error
        except URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                logger.error('uid=%s Service 2 timeout', message.uid)
                raise DownstreamTimeoutException('Превышено время ожидания Сервиса 2') from error
            logger.error('uid=%s Service 2 connection error: %s',
                         message.uid, error.reason)
            raise DownstreamServiceException('Сервис 2 недоступен') from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            logger.error('uid=%s Service 2 returned invalid JSON', message.uid)
            raise DownstreamServiceException('Сервис 2 вернул некорректный JSON') from error
        except (OSError, HTTPException) as error:
            logger.error('uid=%s Service 2 communication error: %s',
                         message.uid, error)
            raise DownstreamServiceException('Соединение с Сервисом 2 прервано') from error
