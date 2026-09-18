from enum import Enum
from typing import Optional


class SuggestionStatusEnum(Enum):
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "under_review"
    TRIAGED = "in_progress"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"

class SuggestionStatus:
    _status: SuggestionStatusEnum
    _reason: Optional[str]

    def __init__(self, status: SuggestionStatusEnum = SuggestionStatusEnum.SUBMITTED, reason: Optional[str] = None) -> None:
        self._status = status
        self._reason = reason

    @property
    def status(self) -> SuggestionStatusEnum:
        return self._status

    @property
    def reason(self) -> Optional[str]:
        return self._reason

    def transition_to(self, status: SuggestionStatusEnum, reason: Optional[str] = None) -> None:
        self._status = status
        self._reason = reason
