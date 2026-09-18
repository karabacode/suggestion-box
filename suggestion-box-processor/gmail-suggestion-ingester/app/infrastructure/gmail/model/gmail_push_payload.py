import base64
import json
from typing import Any
from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class GmailNotificationData(BaseModel):
    """Decoded internal JSON payload sent by the Gmail API."""
    email_address: str = Field(..., alias="emailAddress")
    history_id: int = Field(..., alias="historyId")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("history_id", mode="before")
    @classmethod
    def parse_history_id(cls, value: Any) -> int:
        if isinstance(value, str):
            return int(value)
        return value

class PubSubMessage(BaseModel):
    """The Pub/Sub message object containing the base64-encoded Gmail payload."""
    data: str
    message_id: str
    publish_time: str
    attributes: Optional[Dict[str, str]] = None

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore"  # Ignore any non-standard extra fields from Pub/Sub
    )

    def decode_gmail_data(self) -> GmailNotificationData :
            """Helper method to automatically decode Base64 data into standard JSON or Protobuf email."""

            decoded_bytes = base64.b64decode(self.data)

            # 1. Try standard Gmail API watch payload (JSON)
            try:
                decoded_json = json.loads(decoded_bytes.decode("utf-8"))
                import logging
                logger = logging.getLogger(__name__)
                logger.info("Decoded Gmail data: %s", decoded_json)
                return GmailNotificationData(**decoded_json)
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise ValueError("Failed to decode Gmail data from Pub/Sub message.")


class GmailPushPayload(BaseModel):
    """Outer wrapper for the incoming HTTP POST request from Cloud Pub/Sub."""
    message: PubSubMessage
    subscription: str
    
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore"
    )