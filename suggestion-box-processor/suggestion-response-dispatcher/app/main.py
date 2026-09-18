import base64
import binascii
import logging
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

from schemas.v1 import suggestion_pb2

from .config import Settings
from .gmail_sender import GmailSender
from .oauth import GoogleOAuth
from .response_cache import ResponseCache
from .token_store import TokenStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings.from_environment()
token_store = TokenStore(settings.token_json)
oauth = GoogleOAuth(
    settings.client_secret_json,
    settings.scopes,
    settings.redirect_uri,
    token_store,
)
sender = GmailSender(token_store, settings.scopes)
response_cache = ResponseCache(settings.response_cache_ttl_seconds)
app = FastAPI(title="Suggestion Response Dispatcher", version="0.1.0")
security = HTTPBasic()


def require_maintenance_access(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    if not (
        secrets.compare_digest(credentials.username, "maintenance")
        and secrets.compare_digest(credentials.password, settings.maintenance_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid maintenance credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/auth/start", dependencies=[Depends(require_maintenance_access)])
def auth_start() -> RedirectResponse:
    url, _ = oauth.authorization_url()
    return RedirectResponse(url)


@app.get("/auth/callback")
def auth_callback(
    request: Request,
    code: str = Query(..., min_length=1),
    state: str = Query(..., min_length=1),
) -> dict[str, Any]:
    try:
        token = oauth.exchange_code(str(request.url), state)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        "message": "Authentication succeeded. Copy this token into GMAIL_TOKEN_JSON.",
        "token": token,
    }


@app.post("/webhooks/pubsub")
async def suggestion_analysis(request: Request) -> dict[str, Any]:
    envelope = await request.json()
    encoded_data = envelope.get("message", {}).get("data")
    if not isinstance(encoded_data, str):
        raise HTTPException(status_code=400, detail="Pub/Sub message data is missing")

    analysis = suggestion_pb2.SuggestionAnalysis()
    try:
        analysis.ParseFromString(base64.b64decode(encoded_data, validate=True))
    except (ValueError, binascii.Error) as error:
        raise HTTPException(
            status_code=400, detail="Invalid SuggestionAnalysis protobuf"
        ) from error

    recipient = analysis.original_message.sender_email or analysis.sender_email
    if not recipient or not analysis.draft_reply:
        raise HTTPException(status_code=400, detail="SuggestionAnalysis is incomplete")

    if not response_cache.claim(analysis.email_id):
        logger.info(
            "Skipping duplicate response email_id=%s",
            analysis.email_id,
        )
        return {"accepted": True, "email_id": analysis.email_id, "skipped": True}

    subject = f"Re: {analysis.category or 'Your suggestion'}"
    try:
        sent_id = sender.send(recipient, subject, analysis.draft_reply)
    except Exception as error:
        response_cache.release(analysis.email_id)
        logger.exception("Failed to send suggestion response email_id=%s", analysis.email_id)
        raise HTTPException(status_code=502, detail="Response email delivery failed") from error

    logger.info(
        "Sent suggestion response email_id=%s recipient=%s gmail_message_id=%s",
        analysis.email_id,
        recipient,
        sent_id,
    )
    return {"accepted": True, "email_id": analysis.email_id, "message_id": sent_id}
