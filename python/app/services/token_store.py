from typing import Protocol, runtime_checkable


@runtime_checkable
class TokenStore(Protocol):
    def load(self) -> dict[str, object] | None: ...

    def save(self, token: dict[str, object]) -> None: ...
