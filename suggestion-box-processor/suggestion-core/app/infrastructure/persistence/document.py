from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MessageDocument(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sender: str
    body: str


class StatusDocument(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    reason: str | None = None


class AnalysisDocument(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    suggestion_id: str
    ai_model: str
    agent_version: str
    vibe: str | None
    urgency_level: str | None
    communication_style: str | None
    tags: list[str]
    category: str | None
    suggested_action: str | None
    draft_reply: str | None
    timestamp: datetime


class SuggestionDocument(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_reference: str | None
    message: MessageDocument
    status: StatusDocument
    analyses: list[AnalysisDocument]
