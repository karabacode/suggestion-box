import base64
import binascii
import json
import logging
import time
from email.utils import parseaddr
from threading import Lock
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
        duplicate_sender_ttl_seconds: int = 60,
        ignored_labels: tuple[str, ...] = (
            "SPAM",
            "TRASH",
            "SENT",
            "CATEGORY_PROMOTIONS",
            "CATEGORY_SOCIAL",
            "CATEGORY_UPDATES",
            "CATEGORY_FORUMS",
        ),
    ) -> None:
        self._token_store = token_store
        self._scopes = list(scopes)
        self._email_publisher = email_publisher
        self._history_cursor: str | None = None
        self._duplicate_sender_ttl_seconds = duplicate_sender_ttl_seconds
        self._recent_senders: dict[str, float] = {}
        self._recent_senders_lock = Lock()
        self._ignored_labels = set(ignored_labels)

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
            .watch(
                userId="me",
                body={"topicName": topic_name, "labelIds": ["INBOX"]},
            )
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
            for message_entry in history.get("messagesAdded", []):
                message = message_entry.get("message", {})
                labels = set(message.get("labelIds", []))
                if labels & self._ignored_labels:
                    logger.info(
                        "Skipping added Gmail message email_id=%s labels=%s",
                        message.get("id"),
                        sorted(labels & self._ignored_labels),
                    )
                    continue
                message_id = message.get("id")
                if message_id:
                    message_ids.add(message_id)
        return sorted(message_ids)

    def read_message(self, message_id: str) -> IncomingEmail | None:
        details = (
            self._service()
            .users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        labels = set(details.get("labelIds", []))
        ignored_labels = labels & self._ignored_labels
        if ignored_labels:
            logger.info(
            "Skipping filtered Gmail message email_id=%s labels=%s",
                message_id,
            sorted(ignored_labels),
            )
            return None
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

        if _is_history_at_or_before(history_id, self._history_cursor):
            logger.info(
                "Skipping stale Gmail notification history_id=%s cursor=%s",
                history_id,
                self._history_cursor,
            )
            return PushDeliveryResult(
                accepted=True,
                email_address=email_address,
                history_id=history_id,
                message_ids=[],
            )

        start_history_id = self._history_cursor or _previous_history_id(history_id)
        message_ids = self._process_messages(self.list_history(start_history_id))
        self._history_cursor = _max_history_id(self._history_cursor, history_id)

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
            email = self.read_message(message_id)
            if email is None:
                continue
            sender = _normalize_sender(email.sender_email)
            if not self._claim_sender(sender):
                logger.info(
                    "Skipping duplicate sender within %d seconds sender=%s email_id=%s",
                    self._duplicate_sender_ttl_seconds,
                    sender,
                    email.email_id,
                )
                continue
            logger.info("Forwarding Gmail message email_id=%s to agent topic", message_id)
            self._email_publisher.publish(email)
        return message_ids

    def _claim_sender(self, sender: str) -> bool:
        now = time.monotonic()
        with self._recent_senders_lock:
            self._recent_senders = {
                key: claimed_at
                for key, claimed_at in self._recent_senders.items()
                if now - claimed_at < self._duplicate_sender_ttl_seconds
            }
            if sender in self._recent_senders:
                return False
            self._recent_senders[sender] = now
            return True


def credentials_to_dict(credentials: Credentials) -> dict[str, object]:
    credentials_any = cast(Any, credentials)
    return cast(dict[str, object], json.loads(credentials_any.to_json()))


def _previous_history_id(history_id: str) -> str:
    try:
        return str(max(int(history_id) - 1, 0))
    except ValueError:
        return history_id


def _is_history_at_or_before(history_id: str, cursor: str | None) -> bool:
    if cursor is None:
        return False
    try:
        return int(history_id) <= int(cursor)
    except ValueError:
        return history_id == cursor


def _max_history_id(first: str | None, second: str) -> str:
    if first is None:
        return second
    try:
        return str(max(int(first), int(second)))
    except ValueError:
        return second


def _normalize_sender(sender: str) -> str:
    return (parseaddr(sender)[1] or sender).strip().lower()
