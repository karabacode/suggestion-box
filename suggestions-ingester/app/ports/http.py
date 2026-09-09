import base64
import binascii
from typing import Any

from fastapi import APIRouter, HTTPException
from schemas import suggestion_pb2
from app.services.pubsub import PushHandler

from logging import getLogger

logger = getLogger(__name__)


def create_router(
    pubsub_delivery_handler: PushHandler,
) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        logger.info("Health check requested")
        return {"status": "ok"}

    @router.post("/webhooks/gmail")
    def gmail_push_notification(payload: dict[str, Any]) -> dict[str, object]:
        try:
            result = pubsub_delivery_handler.handle(payload)
        except ValueError as error:
            raise HTTPException(status_code=400, detail="Invalid Gmail notification") from error
        except Exception as error:
            raise HTTPException(status_code=502, detail="Gmail history lookup failed") from error
        print(f"Gmail push notification processed: {result}")
        return {
            "accepted": result.accepted,
            "email_address": result.email_address,
            "history_id": result.history_id,
            "message_ids": result.message_ids,
        }

    @router.post("/webhooks/suggestion-analysis")
    def suggestion_analysis_notification(payload: dict[str, Any]) -> dict[str, object]:
        encoded_data = payload.get("message", {}).get("data")
        if not isinstance(encoded_data, str):
            raise HTTPException(status_code=400, detail="Pub/Sub message data is missing")

        analysis = suggestion_pb2.SuggestionAnalysis()
        try:
            analysis.ParseFromString(base64.b64decode(encoded_data, validate=True))
        except (ValueError, binascii.Error) as error:
            raise HTTPException(status_code=400, detail="Invalid SuggestionAnalysis protobuf") from error
        if not analysis.email_id:
            raise HTTPException(status_code=400, detail="SuggestionAnalysis is incomplete")

        logger.info(f"Suggestion analysis received for email_id={analysis.email_id} with {analysis}")

        return {"accepted": True, "email_id": analysis.email_id}

    return router