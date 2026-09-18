import json
from logging import getLogger
from app.infrastructure.config import settings

logger = getLogger(__name__)

"""
In-memory token store.
This class provides a simple in-memory storage for OAuth refresh token.
"""
class InMemoryTokenStore:
    def __init__(self, token_json: str | None = settings.token_json) -> None:
        self._token = json.loads(token_json) if token_json else None

    def load(self) -> dict[str, object] | None:
        return self._token

    def save(self, token: dict[str, object]) -> None:
        self._token = token
