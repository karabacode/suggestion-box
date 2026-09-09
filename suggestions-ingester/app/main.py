from contextlib import asynccontextmanager
import logging
from typing import Any, cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.infrastructure.auth.google_oauth import GoogleOAuthAdapter
from app.infrastructure.auth.token_store import InMemoryTokenStore
from app.infrastructure.configuration.config import Settings
from app.infrastructure.agent.pubsub_publisher import GooglePubSubEmailPublisher
from app.infrastructure.gmail.google_gmail import GoogleGmailAdapter
from app.ports.auth_http import create_auth_router
from app.ports.http import create_router

logging.basicConfig(level=logging.INFO)


settings = Settings.from_environment()
token_store = InMemoryTokenStore(settings.token_json)
oauth_client = GoogleOAuthAdapter(
    settings.client_secret_json, settings.scopes, settings.redirect_uri, token_store
)
email_publisher = GooglePubSubEmailPublisher(settings.suggestion_agent_topic)
gmail_adapter = GoogleGmailAdapter(token_store, settings.scopes, email_publisher)
pubsub_delivery_handler = gmail_adapter


def _watch_topic() -> str:
    topic = settings.pubsub_topic or "new-email-topic"
    if topic.startswith("projects/"):
        return topic
    if not settings.google_cloud_project:
        raise RuntimeError(
            "GOOGLE_CLOUD_PROJECT is required for a short Pub/Sub topic name"
        )
    return f"projects/{settings.google_cloud_project}/topics/{topic}"


@asynccontextmanager
async def lifespan(_: FastAPI):
    topic = _watch_topic()
    watch = gmail_adapter.start_watch(topic)
    print(f"Gmail watch started for {topic}: {watch}")
    yield

app = FastAPI(title="Suggestion Box API", version="0.1.0", lifespan=lifespan)
app.add_middleware(cast(Any, ProxyHeadersMiddleware), trusted_hosts="*")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://localhost(:\d+)?|chrome-extension://.*",
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)
app.include_router(
    create_router(
        pubsub_delivery_handler,
    )
)
app.include_router(
    create_auth_router(
        oauth_client,
        settings.maintenance_username,
        settings.maintenance_password,
    )
)
