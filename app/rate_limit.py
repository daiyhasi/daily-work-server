import time
from collections import defaultdict, deque
from typing import Deque, DefaultDict

from app.errors import rate_limited


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: DefaultDict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        if self.max_requests <= 0:
            return

        now = time.monotonic()
        hits = self._hits[key]
        cutoff = now - self.window_seconds
        while hits and hits[0] < cutoff:
            hits.popleft()

        if len(hits) >= self.max_requests:
            raise rate_limited()

        hits.append(now)

