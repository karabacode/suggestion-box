from datetime import datetime
from typing import Optional

from app.domain.message import Message


class Analysis:
    _GUARD = object()  # The sentinel token
    _id: str
    _suggestion_id: str
    _vibe: Optional[str] = None
    _urgency_level: Optional[str] = None
    _communication_style: Optional[str] = None
    _tags: list[str] = []
    _category: Optional[str] = None
    _suggested_action: Optional[str] = None
    _draft_reply: Optional[str] = None
    _timestamp: datetime
    _original_message: Optional[Message] = None
    _ai_model: str
    _agent_version: str

    @classmethod
    def create(
        cls,
        id: str,
        suggestion_id: str,
        ai_model: str,
        agent_version: str,
        vibe: Optional[str] = None,
        urgency_level: Optional[str] = None,
        communication_style: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category: Optional[str] = None,
        suggested_action: Optional[str] = None,
        draft_reply: Optional[str] = None,
        original_message: Optional[Message] = None,
    ) -> "Analysis":
        return cls(
            id,
            suggestion_id,
            ai_model,
            agent_version,
            cls._GUARD,
            vibe=vibe,
            urgency_level=urgency_level,
            communication_style=communication_style,
            tags=tags,
            category=category,
            suggested_action=suggested_action,
            draft_reply=draft_reply,
            original_message=original_message,
        )

    def __init__(
        self,
        id: str,
        suggestion_id: str,
        ai_model: str,
        agent_version: str,
        guard: object,
        vibe: Optional[str] = None,
        urgency_level: Optional[str] = None,
        communication_style: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category: Optional[str] = None,
        suggested_action: Optional[str] = None,
        draft_reply: Optional[str] = None,
        original_message: Optional[Message] = None,
    ) -> None:

        if guard is not self._GUARD:
            raise RuntimeError("Direct instantiation of Analysis is not allowed. Use Analysis.create() instead.")

        self._id = id
        self._suggestion_id = suggestion_id
        self._vibe = vibe
        self._urgency_level = urgency_level
        self._communication_style = communication_style
        self._tags = list(tags) if tags is not None else []
        self._category = category
        self._suggested_action = suggested_action
        self._draft_reply = draft_reply
        self._timestamp = datetime.now()
        self._original_message = original_message
        self._ai_model = ai_model
        self._agent_version = agent_version

    @property
    def id(self) -> str:
        return self._id

    @property
    def suggestion_id(self) -> str:
        return self._suggestion_id

    @property
    def vibe(self) -> Optional[str]:
        return self._vibe

    @property
    def urgency_level(self) -> Optional[str]:
        return self._urgency_level

    @property
    def communication_style(self) -> Optional[str]:
        return self._communication_style

    @property
    def tags(self) -> list[str]:
        return list(self._tags)

    @property
    def category(self) -> Optional[str]:
        return self._category

    @property
    def suggested_action(self) -> Optional[str]:
        return self._suggested_action

    @property
    def draft_reply(self) -> Optional[str]:
        return self._draft_reply

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def original_message(self) -> Optional[Message]:
        return self._original_message

    @property
    def ai_model(self) -> str:
        return self._ai_model

    @property
    def agent_version(self) -> str:
        return self._agent_version

    def apply_result(
        self,
        vibe: Optional[str] = None,
        urgency_level: Optional[str] = None,
        communication_style: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category: Optional[str] = None,
        suggested_action: Optional[str] = None,
        draft_reply: Optional[str] = None,
        original_message: Optional[Message] = None,
    ) -> None:
        self._vibe = vibe
        self._urgency_level = urgency_level
        self._communication_style = communication_style
        self._tags = list(tags) if tags is not None else []
        self._category = category
        self._suggested_action = suggested_action
        self._draft_reply = draft_reply
        self._original_message = original_message
        self._timestamp = datetime.now()
