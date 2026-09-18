from logging import getLogger
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, JSONResponse, RedirectResponse
from app.infrastructure.auth.basic_authentication import require_maintenance_access, get_credentials_provider
from app.infrastructure import get_oauth_adapter

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])
logger = getLogger(__name__)


@router.get("/start", dependencies=[Depends(require_maintenance_access)])
def auth_start(oauth_adapter : Annotated[Any, Depends(get_oauth_adapter)]) -> RedirectResponse:
        try:
            authorization_url, _ = oauth_adapter.authorization_url()
            return RedirectResponse(authorization_url)
        except Exception as error:
            raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/callback")
def auth_callback(
     oauth_adapter: Annotated[Any, Depends(get_oauth_adapter)], 
     request: Request,
     state: str = Query(..., min_length=1)) -> JSONResponse:
    
    token = oauth_adapter.exchange_code(str(request.url), state)
    
    return JSONResponse(
        content={
            "message": "Authentication succeeded. Copy the token into GMAIL_TOKEN_JSON for background use.",
            "token": token,
        }
    )