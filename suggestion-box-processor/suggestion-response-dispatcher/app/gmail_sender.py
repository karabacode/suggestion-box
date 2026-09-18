import base64
import json
from email.message import EmailMessage
from typing import Any, cast

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .token_store import TokenStore


class GmailSender:
    def __init__(self, token_store: TokenStore, scopes: tuple[str, ...]) -> None:
        self._token_store = token_store
        self._scopes = scopes

    def send(self, recipient: str, subject: str, body: str) -> str:
        token = self._token_store.load()
        if token is None:
            raise RuntimeError("Gmail send token is not configured")
        credentials_factory = cast(Any, Credentials)
        self._credentials = credentials_factory.from_authorized_user_info(
            token, list(self._scopes)
        )

        if self._credentials.expired and self._credentials.refresh_token:
            self._credentials.refresh(Request())

        service = cast(Any, build)(
            "gmail", "v1", credentials=self._credentials, cache_discovery=False
        )
        message = EmailMessage()
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        encoded = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        response = service.users().messages().send(
            userId="me", body={"raw": encoded}
        ).execute()
        return str(response["id"])
