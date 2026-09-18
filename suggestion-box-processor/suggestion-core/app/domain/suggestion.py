from typing import Optional
from uuid import UUID, uuid4

from app.domain.analysis import Analysis
from app.domain.message import Message
from app.domain.suggestion_status import SuggestionStatus, SuggestionStatusEnum


"""
Root aggregate for the Suggestion entity
"""
class Suggestion:
    _GUARD = object()  # The sentinel token
    _id: UUID
    _external_reference: Optional[str]
    _message: Message
    _status: SuggestionStatus
    _analyses: list[Analysis]


    @classmethod
    def create(cls, sender: str, body: str, external_reference: Optional[str] = None) -> "Suggestion":
        message = Message.create(sender, body, id=None)
        suggestion = cls(message, cls._GUARD, external_reference)
        return suggestion


    def __init__(self, message: Message, guard: object, external_reference: Optional[str] = None) -> None:

        if guard is not self._GUARD:
            raise RuntimeError("Direct instantiation of Suggestion is not allowed. Use Suggestion.create() instead.")

        self._id = uuid4()
        self._message = message
        self._external_reference = external_reference
        self._status = SuggestionStatus()
        self._analyses = []

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def message(self) -> Message:
        return self._message

    @property
    def external_reference(self) -> Optional[str]:
        return self._external_reference

    @property
    def status(self) -> SuggestionStatus:
        return self._status

    @property
    def analyses(self) -> list[Analysis]:
        return list(self._analyses)

    def add_analysis(self, analysis: Analysis) -> None:
        self._analyses.append(analysis)

    def update_status(self, status: SuggestionStatusEnum, reason: Optional[str] = None) -> None:
        self._status.transition_to(status, reason)
