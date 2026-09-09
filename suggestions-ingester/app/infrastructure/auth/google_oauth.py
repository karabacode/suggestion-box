import json
from typing import Any, cast

from google_auth_oauthlib.flow import Flow

from app.services.oauth import OAuthClient
from app.services.token_store import TokenStore


class GoogleOAuthAdapter(OAuthClient):
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

    def _flow(self, state: str | None = None) -> Flow:
        flow_type = cast(Any, Flow)
        return cast(
            Flow,
            flow_type.from_client_config(
            client_config=self._client_config,
            scopes=self._scopes,
            redirect_uri=self._redirect_uri,
            state=state,
            code_verifier=self._code_verifier,
            autogenerate_code_verifier=self._code_verifier is None,
            ),
        )

    def authorization_url(self) -> tuple[str, str]:
        flow = self._flow()
        flow_any = cast(Any, flow)
        url, state = cast(
            tuple[str, str],
            flow_any.authorization_url(
                access_type="offline",
                prompt="consent",
            ),
        )
        self._state = state
        self._code_verifier = cast(Any, flow).code_verifier
        return url, state

    def exchange_code(self, authorization_response: str, state: str) -> dict[str, object]:
        if self._state is None or state != self._state:
            raise ValueError("OAuth state is invalid or expired")

        flow = self._flow(state=state)
        print(f"Exchanging code for token with authorization_response: {state}")
        print(f"Authorization response: {authorization_response}")
        flow_any = cast(Any, flow)
        flow_any.fetch_token(authorization_response=authorization_response)
        token_json = flow_any.credentials.to_json()
        token = cast(dict[str, object], json.loads(token_json))
        self._token_store.save(token)
        self._state = None
        self._code_verifier = None
        return token
