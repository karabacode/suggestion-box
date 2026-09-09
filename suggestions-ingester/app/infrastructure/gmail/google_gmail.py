import base64
import binascii
import json
import logging
from typing import Any, cast

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # pyright: ignore[reportUnknownVariableType]

from app.services.pubsub import PushDeliveryResult, PushHandler
from app.services.agent import EmailPublisher
from app.services.email import IncomingEmail

logger = logging.getLogger(__name__)
from app.services.token_store import TokenStore


class GoogleGmailAdapter(PushHandler):
    def __init__(
        self,
        token_store: TokenStore,
        scopes: tuple[str, ...],
        email_publisher: EmailPublisher | None = None,
    ) -> None:
        self._token_store = token_store
        self._scopes = list(scopes)
        self._email_publisher = email_publisher
        self._history_cursor: str | None = None

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
        watch = (
            self._service()
            .users()
            .watch(userId="me", body={"topicName": topic_name})
            .execute()
        )
        history_id = watch.get("historyId")
        if isinstance(history_id, str):
            self._history_cursor = history_id
        return watch

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

    def read_message(self, message_id: str) -> IncomingEmail:
        details = (
            self._service()
            .users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        headers = details.get("payload", {}).get("headers", [])
        sender = next(
            (
                header.get("value", "")
                for header in headers
                if header.get("name", "").lower() == "from"
            ),
            "",
        )
        body = self._message_body(details.get("payload", {})) or details.get(
            "snippet", ""
        )
        email = IncomingEmail(message_id, sender, body)
        logger.info(
            "Retrieved Gmail message email_id=%s sender=%s body_chars=%d",
            email.email_id,
            email.sender_email,
            len(email.body),
        )
        return email

    def _message_body(self, payload: dict[str, Any]) -> str:
        body_data = payload.get("body", {}).get("data")
        if isinstance(body_data, str):
            return base64.urlsafe_b64decode(body_data + "===").decode(
                "utf-8", errors="replace"
            )
        for part in payload.get("parts", []):
            if isinstance(part, dict):
                body = self._message_body(part)
                if body:
                    return body
        return ""

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

        logger.info(
            "Received Gmail notification email_address=%s history_id=%s",
            email_address,
            history_id,
        )

        start_history_id = self._history_cursor or _previous_history_id(history_id)
        message_ids = self._process_messages(self.list_history(start_history_id))
        self._history_cursor = history_id

        return PushDeliveryResult(
            accepted=True,
            email_address=email_address,
            history_id=history_id,
            message_ids=message_ids,
        )

    def _process_messages(self, message_ids: list[str]) -> list[str]:
        if self._email_publisher is None:
            return message_ids
        for message_id in message_ids:
            logger.info("Forwarding Gmail message email_id=%s to agent topic", message_id)
            self._email_publisher.publish(self.read_message(message_id))
        return message_ids


def credentials_to_dict(credentials: Credentials) -> dict[str, object]:
    credentials_any = cast(Any, credentials)
    return cast(dict[str, object], json.loads(credentials_any.to_json()))


def _previous_history_id(history_id: str) -> str:
    try:
        return str(max(int(history_id) - 1, 0))
    except ValueError:
        return history_id
