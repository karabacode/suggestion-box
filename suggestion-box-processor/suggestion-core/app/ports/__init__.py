from fastapi import APIRouter

from app.ports.v1.suggestions import router as suggestions_router_v1
from app.ports.health import router as health_router

api_router = APIRouter()
api_router.include_router(suggestions_router_v1)
api_router.include_router(health_router)

