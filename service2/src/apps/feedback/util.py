from datetime import UTC, datetime

from django.utils import timezone


class DateTimeUtil:
    @staticmethod
    def format_utc(value: datetime | None = None) -> str:
        value = value if value is not None else timezone.now()
        return value.astimezone(UTC).isoformat(
            timespec='milliseconds').replace('+00:00', 'Z')
