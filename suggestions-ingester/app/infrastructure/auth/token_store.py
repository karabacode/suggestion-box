import json

from app.services.token_store import TokenStore


class InMemoryTokenStore(TokenStore):
    def __init__(self, token_json: str | None = None) -> None:
        self._token = json.loads(token_json) if token_json else None

    def load(self) -> dict[str, object] | None:
        return self._token

    def save(self, token: dict[str, object]) -> None:
        self._token = token
