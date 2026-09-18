from contextlib import asynccontextmanager
import logging
from typing import Any, cast

from fastapi import FastAPI
from app.ports import api_router as http_router_v1, health_router, auth_router_v1
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.infrastructure import get_gmail_adapter
from app.infrastructure.config import settings


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    topic = settings.pubsub_topic
    if not topic:
        raise RuntimeError("PUBSUB_TOPIC is required")
    gmail_adapter = get_gmail_adapter()
    try:
        logger.info("Attempting to start Gmail push watch...")
        watch = gmail_adapter.start_watch(topic)
        logger.info("Gmail watch response: %s", watch)
        gmail_adapter.last_known_history_id = int(str(watch.get("historyId")))
        logger.info("Gmail watch started successfully on topic %s", topic)
    except RuntimeError as e:
        logger.warning(
            "Skipping initial Gmail watch: %s. Please authenticate via"
            " /v1/auth/start.",e)
    yield

app = FastAPI(title="Suggestion Core", version="0.1.0", lifespan=lifespan)

app.add_middleware(cast(Any, ProxyHeadersMiddleware), trusted_hosts="*")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://localhost(:\d+)?|chrome-extension://.*",
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)
app.include_router(http_router_v1)
app.include_router(health_router)
app.include_router(auth_router_v1)

from fastapi.exceptions import RequestValidationError
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("422 Validation Error: %s | Body: %s", exc.errors(), await request.body())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
