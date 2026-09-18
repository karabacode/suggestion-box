import json
from typing import Any, cast
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.infrastructure.auth.token_store import InMemoryTokenStore


class GoogleOAuthAdapter:
    def __init__(
        self,
        client_secret_json: str,
        scopes: tuple[str, ...] | list[str],
        redirect_uri: str,
        token_store: InMemoryTokenStore,
    ) -> None:
        self._client_config = json.loads(client_secret_json)
        self._scopes = list(scopes)
        self._redirect_uri = redirect_uri
        self._token_store = token_store

    def _flow(self, state: str | None = None, code_verifier: str | None = None) -> Flow:
        return Flow.from_client_config(
            client_config=self._client_config,
            scopes=self._scopes,
            redirect_uri=self._redirect_uri,
            state=state,
            code_verifier=code_verifier,
            autogenerate_code_verifier=False,  # Prevents code_verifier state mismatch across workers
        )

    def authorization_url(self) -> tuple[str, str]:
        flow = self._flow()
        url, state = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
        )
        return url, state

    def exchange_code(self, authorization_response: str, state: str) -> dict[str, object]:
        # Initialize flow with state; no local instance memory dependency
        flow = self._flow(state=state)
        flow.fetch_token(authorization_response=authorization_response)
        
        token_json = flow.credentials.to_json()
        token = cast(dict[str, object], json.loads(token_json))
        
        # Persist updated token payload (containing refresh_token)
        self._token_store.save(token)
        return token

    def getCredentials(self) -> Credentials:
        token = self._token_store.load()
        if token is None:
            raise RuntimeError("Gmail is not authenticated; visit /auth/start first")
        
        credentials = Credentials.from_authorized_user_info(token, self._scopes)
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(GoogleRequest())
            # Save refreshed credentials back to store
            self._token_store.save(json.loads(credentials.to_json()))
            
        return credentials