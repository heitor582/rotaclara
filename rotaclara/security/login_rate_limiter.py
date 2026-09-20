from threading import Lock

from .errors import LoginLimitExceeded

class LoginRateLimiter:
    def __init__(self, maximum_attempts=10, window_seconds=300):
        self.maximum_attempts = maximum_attempts
        self.window_seconds = window_seconds
        self.attempts = {}
        self.lock = Lock()

    def check(self, client, timestamp):
        with self.lock:
            self.attempts = {key: [attempt for attempt in attempts if attempt > timestamp - self.window_seconds]
                             for key, attempts in self.attempts.items() if attempts[-1] > timestamp - self.window_seconds}
            if len(self.attempts.get(client, [])) >= self.maximum_attempts:
                raise LoginLimitExceeded('Muitas tentativas. Aguarde cinco minutos.')

    def record_failure(self, client, timestamp):
        with self.lock:
            self.attempts.setdefault(client, []).append(timestamp)

    def clear(self, client):
        with self.lock:
            self.attempts.pop(client, None)
