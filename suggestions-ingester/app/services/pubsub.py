from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class PushDeliveryResult:
    accepted: bool
    email_address: str
    history_id: str
    message_ids: list[str]


@runtime_checkable
class PushHandler(Protocol):
    def handle(self, envelope: dict[str, Any]) -> PushDeliveryResult: ...

    def start_watch(self, topic_name: str) -> dict[str, object]: ...

    def list_history(self, history_id: str) -> list[str]: ...
