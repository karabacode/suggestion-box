import secrets
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse

from app.services.oauth import OAuthClient


def create_auth_router(
    oauth_adapter: OAuthClient,
    maintenance_username: str,
    maintenance_password: str,
) -> APIRouter:
    router = APIRouter()
    security = HTTPBasic()

    def require_maintenance_access(
        credentials: HTTPBasicCredentials = Depends(security),
    ) -> None:
        valid_username = secrets.compare_digest(
            credentials.username, maintenance_username
        )
        valid_password = secrets.compare_digest(
            credentials.password, maintenance_password
        )
        if not (valid_username and valid_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid maintenance credentials",
                headers={"WWW-Authenticate": "Basic"},
            )

    @router.get("/auth/start", dependencies=[Depends(require_maintenance_access)])
    def auth_start() -> RedirectResponse:
        try:
            authorization_url, _ = oauth_adapter.authorization_url()
            return RedirectResponse(authorization_url)
        except Exception as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    @router.get("/auth/callback")
    def auth_callback(
        request: Request,
        code: str = Query(..., min_length=1),
        state: str = Query(..., min_length=1),
    ) -> dict[str, Any]:
        try:
            token = oauth_adapter.exchange_code(str(request.url), state)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            print(f"OAuth exchange failed: {error}")
            raise HTTPException(status_code=400, detail="OAuth exchange failed") from error

        return {
            "message": "Authentication succeeded. Copy the token into GMAIL_TOKEN_JSON for background use.",
            "token": token,
        }

    return router