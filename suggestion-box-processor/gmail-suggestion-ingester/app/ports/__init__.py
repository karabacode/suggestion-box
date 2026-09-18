from fastapi import APIRouter

from app.ports.v1.emails import router as http_router_v1
from app.ports.health import router as health_router
from app.ports.v1.auth import router as auth_router_v1
api_router = APIRouter()
api_router.include_router(http_router_v1)
api_router.include_router(health_router)
api_router.include_router(auth_router_v1)