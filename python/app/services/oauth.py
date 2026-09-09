from typing import Protocol, runtime_checkable


@runtime_checkable
class OAuthClient(Protocol):
    def authorization_url(self) -> tuple[str, str]: ...

    def exchange_code(self, authorization_response: str, state: str) -> dict[str, object]: ...
