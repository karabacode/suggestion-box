import time
from threading import Lock


class ResponseCache:
    def __init__(self, ttl_seconds: int = 86400) -> None:
        self._ttl_seconds = ttl_seconds
        self._entries: dict[str, float] = {}
        self._lock = Lock()

    def claim(self, email_id: str) -> bool:
        now = time.monotonic()
        with self._lock:
            self._remove_expired(now)
            if email_id in self._entries:
                return False
            self._entries[email_id] = now
            return True

    def release(self, email_id: str) -> None:
        with self._lock:
            self._entries.pop(email_id, None)

    def _remove_expired(self, now: float) -> None:
        expired = [
            email_id
            for email_id, claimed_at in self._entries.items()
            if now - claimed_at >= self._ttl_seconds
        ]
        for email_id in expired:
            del self._entries[email_id]
