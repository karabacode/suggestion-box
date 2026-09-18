import json
from typing import Any, cast

from google_auth_oauthlib.flow import Flow

from .token_store import TokenStore


class GoogleOAuth:
    def __init__(
        self,
        client_secret_json: str,
        scopes: tuple[str, ...],
        redirect_uri: str,
        token_store: TokenStore,
    ) -> None:
        self._client_config = json.loads(client_secret_json)
        self._scopes = list(scopes)
        self._redirect_uri = redirect_uri
        self._token_store = token_store
        self._state: str | None = None
        self._code_verifier: str | None = None

    def authorization_url(self) -> tuple[str, str]:
        flow = cast(Any, Flow).from_client_config(
            self._client_config,
            scopes=self._scopes,
            redirect_uri=self._redirect_uri,
            autogenerate_code_verifier=True,
        )
        url, state = flow.authorization_url(
            access_type="offline",
            prompt="consent",
        )
        self._state = state
        self._code_verifier = flow.code_verifier
        return str(url), str(state)

    def exchange_code(self, authorization_response: str, state: str) -> dict[str, object]:
        if self._state is None or state != self._state:
            raise ValueError("OAuth state is invalid or expired")
        flow = cast(Any, Flow).from_client_config(
            self._client_config,
            scopes=self._scopes,
            redirect_uri=self._redirect_uri,
            state=state,
            code_verifier=self._code_verifier,
            autogenerate_code_verifier=False,
        )
        flow.fetch_token(authorization_response=authorization_response)
        token = cast(dict[str, object], json.loads(flow.credentials.to_json()))
        self._token_store.save(token)
        self._state = None
        self._code_verifier = None
        return token
