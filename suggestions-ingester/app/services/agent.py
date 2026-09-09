from typing import Protocol, runtime_checkable

from app.services.email import IncomingEmail


@runtime_checkable
class EmailPublisher(Protocol):
    def publish(self, email: IncomingEmail) -> None: ...
