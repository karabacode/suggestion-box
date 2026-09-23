from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from app.infrastructure import get_gmail_adapter, get_pubsub_email_publisher
from typing import Annotated
from logging import getLogger

from app.infrastructure.pubsub_publisher import PubSubEmailPublisher
from app.infrastructure.gmail.model.gmail_push_payload import GmailPushPayload
from app.infrastructure.gmail.google_gmail_adapter import GoogleGmailAdapter

logger = getLogger(__name__)
router = APIRouter(prefix="/v1/emails", tags=["Suggestions"])

"""
Email ingestion endpoint for Gmail push notifications with protobuf.
"""
@router.post("/", status_code=201)
def ingest_email(
    payload: GmailPushPayload, 
    googleGmailAdapter: Annotated[GoogleGmailAdapter, Depends(get_gmail_adapter)],
    publisher: Annotated[PubSubEmailPublisher, Depends(get_pubsub_email_publisher)]
) -> JSONResponse:
    logger.info("Received Gmail push payload %s", payload)
    notification = payload.message.decode_gmail_data()
    notifications = googleGmailAdapter.handle(notification)
    logger.info("Processed notification %s", notifications)
    for notification in notifications:
        publisher.publish(notification)
    return JSONResponse(content={"accepted": True})
