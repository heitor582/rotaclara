from datetime import datetime, timezone

from .domain import LOCAL_TIMEZONE


class SystemClock:
    def now(self):
        return datetime.now(timezone.utc)

    def today(self):
        return self.now().astimezone(LOCAL_TIMEZONE).date().isoformat()

    def timestamp(self):
        return self.now().isoformat(timespec='seconds')
