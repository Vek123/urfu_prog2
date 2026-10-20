from datetime import UTC, datetime


class DateTimeUtil:
    @staticmethod
    def format_utc(value: datetime | None = None) -> str:
        value = value if value is not None else datetime.now(UTC)
        return value.astimezone(UTC).isoformat(
            timespec='milliseconds').replace('+00:00', 'Z')
