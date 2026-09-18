from typing import Optional
from uuid import UUID, uuid4

class Message:
    _GUARD = object()  # The sentinel token
    _id: Optional[UUID]
    _sender: str
    _body: str

    @classmethod
    def create(cls, sender: str, body: str, id: Optional[UUID] = None) -> "Message":
        return cls(id, sender, body, cls._GUARD)

    def __init__(self, id: Optional[UUID], sender: str, body: str, guard: object) -> None:

        if guard is not self._GUARD:
            raise RuntimeError("Direct instantiation of Message is not allowed. Use Message.create() instead.")

        from uuid import uuid4
        self._id = id or uuid4()
        self._sender = sender
        self._body = body

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def sender(self) -> str:
        return self._sender

    @property
    def body(self) -> str:
        return self._body
