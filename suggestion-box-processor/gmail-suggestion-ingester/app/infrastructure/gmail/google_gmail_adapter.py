import base64
import logging
from threading import Lock
from typing import Any, cast
from app.infrastructure.gmail.google_oauth_adapter import GoogleOAuthAdapter
from app.infrastructure.config import settings
from googleapiclient.discovery import build  # pyright: ignore[reportUnknownVariableType]

from app.infrastructure.gmail.model.gmail_push_payload import GmailNotificationData
from app.schemas.v1.submit_suggestion_dto_p2p import SubmitSuggestionDto

logger = logging.getLogger(__name__)

class GoogleGmailAdapter:

    last_known_history_id: int = 0
    def __init__(
        self,
        oauth_provider: GoogleOAuthAdapter,
        duplicate_sender_ttl_seconds: int = settings.duplicate_sender_ttl_seconds,
        ignored_labels: tuple[str, ...] = settings.ignored_gmail_labels,
    ) -> None:
        logger.info("Initializing GoogleGmailAdapter")
        self._oauth_provider = oauth_provider
        self._duplicate_sender_ttl_seconds = duplicate_sender_ttl_seconds
        self._recent_senders: dict[str, float] = {}
        self._recent_senders_lock = Lock()
        self._ignored_labels = set(ignored_labels)

    def _service(self) -> Any:
        credentials = self._oauth_provider.getCredentials()
        build_service = cast(Any, build)
        return build_service("gmail", "v1", credentials=credentials, cache_discovery=False)

    def start_watch(self, topic_name: str) -> dict[str, object]:
        return (
            self._service()
            .users()
            .watch(
                userId="me",
                body={"topicName": topic_name, "labelIds": ["INBOX"]},
            )
            .execute()
        )

    def _read_message(self, message_id: str) -> SubmitSuggestionDto | None:
        details = (
            self._service()
            .users()
            .messages()
            .get(userId="me", id=message_id)
            .execute()
        )
        labels = set(details.get("labelIds", []))
        ignored_labels = labels & self._ignored_labels
        if ignored_labels:
            logger.info(
            "Skipping filtered Gmail message message_id=%s labels=%s",
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
        logger.info(
            "Retrieved Gmail message message_id=%s sender=%s body_chars=%d",
            message_id,
            sender,
            len(body),
        )
        return SubmitSuggestionDto.model_validate({
            "sender": sender,
            "body": body,
            "external_reference": message_id
        })

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

    """
    Handle incoming Gmail notifications and extract relevant message details.
    """
    def handle(self, gmailNotificationData: GmailNotificationData | None) -> list[SubmitSuggestionDto]:
        if gmailNotificationData is None:
            logger.info("Received empty Gmail notification")
            return []

        email_address = gmailNotificationData.email_address
        history_id = gmailNotificationData.history_id

        logger.info(
            "Received Gmail notification email_address=%s history_id=%s",
            email_address,
            history_id,
        )

        message_ids = self._get_message_ids_from_history(self.last_known_history_id)
        self.last_known_history_id = history_id
        if not message_ids:
            logger.info("No new messages found for history_id=%s", history_id)
            return []

        suggestions: list[SubmitSuggestionDto] = []
        for message_id in message_ids:
            suggestion = self._process_single_message(message_id)
            if suggestion:
                suggestions.append(suggestion)

        return suggestions


    def _get_message_ids_from_history(self, start_history_id: int) -> list[str]:
        """Fetches history records and extracts unique added message IDs."""
        credentials = self._oauth_provider.getCredentials()
        service = build("gmail", "v1", credentials=credentials)

        try:
            history_response = (
                service.users()
                .history()
                .list(
                    userId="me",
                    startHistoryId=start_history_id,
                    historyTypes=["messageAdded"],
                )
                .execute()
            )
        except Exception as exc:
            logger.error("Failed to fetch Gmail history startHistoryId=%s: %s", start_history_id, exc)
            return []

        history_records = history_response.get("history", [])
        unique_message_ids: set[str] = set()

        for record in history_records:
            for message_added in record.get("messagesAdded", []):
                msg_id = message_added.get("message", {}).get("id")
                if msg_id:
                    unique_message_ids.add(msg_id)

        return list(unique_message_ids)


    def _process_single_message(
        self, message_id: str
    ) -> SubmitSuggestionDto | None:
        """Reads a single Gmail message and converts it to a SubmitSuggestionDto."""
        message_detail = self._read_message(message_id)
        if not message_detail:
            return None

        # Control stale history_Id
        # Control same sender within the duplicate_sender_ttl_seconds window

        return message_detail
