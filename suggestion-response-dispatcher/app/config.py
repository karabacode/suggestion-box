import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    token_json: str | None
    client_secret_json: str
    redirect_uri: str
    maintenance_password: str
    response_cache_ttl_seconds: int
    scopes: tuple[str, ...]

    @classmethod
    def from_environment(cls) -> "Settings":
        token_json = os.getenv("GMAIL_TOKEN_JSON")
        client_secret_json = os.getenv("GOOGLE_CLIENT_SECRET_JSON")
        if not client_secret_json:
            raise RuntimeError("GOOGLE_CLIENT_SECRET_JSON is required")
        try:
            json.loads(client_secret_json)
        except json.JSONDecodeError as error:
            raise RuntimeError("GOOGLE_CLIENT_SECRET_JSON is not valid JSON") from error
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
        maintenance_password = os.getenv("MAINTENANCE_PASSWORD")
        if not redirect_uri or not maintenance_password:
            raise RuntimeError("GOOGLE_REDIRECT_URI and MAINTENANCE_PASSWORD are required")

        scopes = tuple(
            scope.strip()
            for scope in os.getenv(
                "GMAIL_SCOPES", "https://www.googleapis.com/auth/gmail.send"
            ).split(",")
            if scope.strip()
        )
        return cls(
            token_json=token_json,
            client_secret_json=client_secret_json,
            redirect_uri=redirect_uri,
            maintenance_password=maintenance_password,
            response_cache_ttl_seconds=int(os.getenv("RESPONSE_CACHE_TTL_SECONDS", "60")),
            scopes=scopes,
        )
