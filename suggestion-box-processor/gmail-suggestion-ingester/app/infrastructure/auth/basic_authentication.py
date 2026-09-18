
import secrets
from fastapi import Depends, HTTPException, status
from typing import Annotated
from fastapi.security import HTTPBasicCredentials
from app.infrastructure import get_credentials_provider, get_credentials_store
from logging import getLogger

logger = getLogger(__name__)

"""
Basic authentication for maintenance access. 
This function is used in the FastAPI endpoint annotation in the dependency parameter.
"""
def require_maintenance_access(
        credentials: Annotated[HTTPBasicCredentials, Depends(get_credentials_provider())]) -> None:
    
    maintenance_credentials = get_credentials_store().find_by_user_name("maintenance") or {}
    maintenance_username : str = maintenance_credentials.get("maintenance_username") or ""
    maintenance_password : str = maintenance_credentials.get("maintenance_password") or ""

    valid_username = secrets.compare_digest(credentials.username, maintenance_username)
    valid_password = secrets.compare_digest(credentials.password, maintenance_password)

    if not (valid_username and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid maintenance credentials",
            headers={"WWW-Authenticate": "Basic"},
        )