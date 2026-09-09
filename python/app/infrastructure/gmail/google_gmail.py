import base64
import binascii
import json
from typing import Any, cast

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # pyright: ignore[reportUnknownVariableType]

from app.services.pubsub import PushDeliveryResult, PushHandler
from app.services.token_store import TokenStore


class GoogleGmailAdapter(PushHandler):
    def __init__(self, token_store: TokenStore, scopes: tuple[str, ...]) -> None:
        self._token_store = token_store
        self._scopes = list(scopes)

    def _service(self) -> Any:
        token = self._token_store.load()
        if token is None:
            raise RuntimeError("Gmail is not authenticated; visit /auth/start first")

        credentials_factory = cast(Any, Credentials)
        credentials = credentials_factory.from_authorized_user_info(token, self._scopes)
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(GoogleRequest())
            self._token_store.save(credentials_to_dict(credentials))

        build_service = cast(Any, build)
        return build_service("gmail", "v1", credentials=credentials, cache_discovery=False)

    def start_watch(self, topic_name: str) -> dict[str, object]:
        return (
            self._service()
            .users()
            .watch(userId="me", body={"topicName": topic_name})
            .execute()
        )

    def list_history(self, history_id: str) -> list[str]:
        response = cast(
            dict[str, Any],
            (
            self._service()
            .users()
            .history()
            .list(userId="me", startHistoryId=history_id)
            .execute()
            ),
        )
        message_ids: set[str] = set()
        print(f"Received Gmail history response: {response}")
        for history in response.get("history", []):
            for message in history.get("messages", []):
                message_id = message.get("id")
                if message_id:
                    message_ids.add(message_id)
        return sorted(message_ids)

    def handle(self, envelope: dict[str, object]) -> PushDeliveryResult:
        message = envelope.get("message", {})
        if not isinstance(message, dict):
            raise ValueError("Pub/Sub message data is missing")
        message = cast(dict[str, Any], message)
        encoded_data = message.get("data")
        if not isinstance(encoded_data, str):
            raise ValueError("Pub/Sub message data is missing")

        try:
            notification = json.loads(base64.b64decode(encoded_data).decode("utf-8"))
            email_address = str(notification["emailAddress"])
            history_id = str(notification["historyId"])
        except (
            KeyError,
            TypeError,
            ValueError,
            UnicodeDecodeError,
            binascii.Error,
            json.JSONDecodeError,
        ) as error:
            raise ValueError("Invalid Gmail notification") from error

        return PushDeliveryResult(
            accepted=True,
            email_address=email_address,
            history_id=history_id,
            message_ids=self.list_history(history_id),
        )


def credentials_to_dict(credentials: Credentials) -> dict[str, object]:
    credentials_any = cast(Any, credentials)
    return cast(dict[str, object], json.loads(credentials_any.to_json()))
