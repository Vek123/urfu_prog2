import logging

from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)
RECEIVED_AT_HEADER = 'X-Service1-Received-At-Ns'


def log_delivery_timing(request, received_at_ns):
    raw_timestamp = request.headers.get(RECEIVED_AT_HEADER)
    if raw_timestamp is None:
        logger.info('Direct request: delivery time unavailable without %s',
                    RECEIVED_AT_HEADER)
        return
    if (not raw_timestamp.isascii() or not raw_timestamp.isdecimal()
            or len(raw_timestamp) > 20):
        raise ValidationError({RECEIVED_AT_HEADER: ['ожидается временная отметка в наносекундах']})
    started_at_ns = int(raw_timestamp)
    if not 0 < started_at_ns <= received_at_ns:
        raise ValidationError({RECEIVED_AT_HEADER: ['отметка должна быть положительной и не из будущего']})
    elapsed_ms = (received_at_ns - started_at_ns) / 1_000_000
    uid = request.data.get('uid', '') if isinstance(request.data, dict) else ''
    logger.info('uid=%s request delivery elapsed_ms=%.3f '
                'service1_received_at_ns=%d service2_received_at_ns=%d',
                uid, elapsed_ms, started_at_ns, received_at_ns)
