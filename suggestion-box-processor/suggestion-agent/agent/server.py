import base64
import binascii
import logging
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request
from google.protobuf.json_format import MessageToDict
from pydantic import BaseModel, Field

from schemas.v1 import suggestion_pb2

from .core import SuggestionAgent
from .config import AgentSettings
from .pubsub_publisher import SuggestionPublisher

logger = logging.getLogger(__name__)


class EmailAnalysisRequest(BaseModel):
    email_id: str = Field(min_length=1)
    sender_email: str = Field(min_length=1)
    email_body: str = Field(min_length=1)


class SuggestionAnalysisResponse(BaseModel):
    analysis: dict[str, Any]


def create_app(
    agent: SuggestionAgent | None = None,
    publisher: SuggestionPublisher | None = None,
) -> FastAPI:
    resolved_agent = agent or SuggestionAgent()
    resolved_publisher = publisher or SuggestionPublisher(AgentSettings().output_topic)
    app = FastAPI(title="Suggestion Agent", version="0.1.0")
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/analyze", response_model=SuggestionAnalysisResponse)
    def analyze_email(payload: EmailAnalysisRequest) -> SuggestionAnalysisResponse:
        try:
            analysis = resolved_agent.process(
                payload.email_id,
                payload.sender_email,
                payload.email_body,
            )
        except Exception as error:
            raise HTTPException(status_code=502, detail="Agent analysis failed") from error

        try:
            resolved_publisher.publish(analysis)
        except Exception as error:
            raise HTTPException(status_code=502, detail="Analysis publishing failed") from error

        return SuggestionAnalysisResponse(
            analysis=MessageToDict(analysis, preserving_proto_field_name=True)
        )

    @router.post("/webhooks/pubsub")
    async def pubsub_email(request: Request) -> dict[str, Any]:
        envelope = await request.json()
        encoded_data = envelope.get("message", {}).get("data")
        if not isinstance(encoded_data, str):
            raise HTTPException(status_code=400, detail="Pub/Sub message data is missing")

        email = suggestion_pb2.EmailMessage()
        print(f"Pub/Sub email message received for email {email} with email_id: {email.email_id}")
        try:
            email.ParseFromString(base64.b64decode(encoded_data, validate=True))
        except (ValueError, binascii.Error) as error:
            raise HTTPException(status_code=400, detail="Invalid EmailMessage protobuf") from error
        if not email.email_id or not email.sender_email or not email.body:
            raise HTTPException(status_code=400, detail="EmailMessage is incomplete")

        logger.info(
            "Received EmailMessage email_id=%s sender=%s body_chars=%d",
            email.email_id,
            email.sender_email,
            len(email.body),
        )

        try:
            analysis = resolved_agent.process(
                email.email_id,
                email.sender_email,
                email.body,
            )
            logger.info("Generated SuggestionAnalysis email_id=%s", email.email_id)
        except Exception as error:
            raise HTTPException(status_code=502, detail="Agent analysis failed") from error

        try:
            resolved_publisher.publish(analysis)
        except Exception as error:
            raise HTTPException(status_code=502, detail="Analysis publishing failed") from error

        return {
            "accepted": True,
            "analysis": MessageToDict(analysis, preserving_proto_field_name=True),
        }

    app.include_router(router)
    return app
