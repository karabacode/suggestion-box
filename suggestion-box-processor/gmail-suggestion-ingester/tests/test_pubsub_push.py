import base64
import json
import unittest

from app.infrastructure.gmail.google_gmail import GoogleGmailAdapter
from app.services.email import IncomingEmail


class FakeGmailAdapter(GoogleGmailAdapter):
    def __init__(self) -> None:
        self.history_ids: list[str] = []
        self._email_publisher = None
        self._history_cursor = None

    def list_history(self, history_id: str) -> list[str]:
        self.history_ids.append(history_id)
        return ["message-1"]


class FakePublisher:
    def __init__(self) -> None:
        self.emails: list[IncomingEmail] = []

    def publish(self, email: IncomingEmail) -> None:
        self.emails.append(email)


class PubSubPushTests(unittest.TestCase):
    def test_ignores_stale_notification_without_querying_history(self) -> None:
        adapter = FakeGmailAdapter()
        adapter._history_cursor = "300"
        notification = {"emailAddress": "user@example.com", "historyId": "299"}
        envelope = {
            "message": {
                "data": base64.b64encode(json.dumps(notification).encode()).decode()
            }
        }

        result = adapter.handle(envelope)

        self.assertTrue(result.accepted)
        self.assertEqual(result.message_ids, [])
        self.assertEqual(adapter.history_ids, [])

    def test_skips_sent_message_before_publishing(self) -> None:
        publisher = FakePublisher()
        adapter = GoogleGmailAdapter(
            token_store=None,  # type: ignore[arg-type]
            scopes=(),
            email_publisher=publisher,
        )
        adapter._service = lambda: _FakeGmailService(
            {"labelIds": ["SENT", "INBOX"]}
        )

        adapter._process_messages(["sent-message"])

        self.assertEqual(publisher.emails, [])

    def test_skips_promotions_message_before_publishing(self) -> None:
        publisher = FakePublisher()
        adapter = GoogleGmailAdapter(
            token_store=None,  # type: ignore[arg-type]
            scopes=(),
            email_publisher=publisher,
        )
        adapter._service = lambda: _FakeGmailService(
            {"labelIds": ["CATEGORY_PROMOTIONS", "INBOX"]}
        )

        adapter._process_messages(["promotion-message"])

        self.assertEqual(publisher.emails, [])

    def test_suppresses_same_sender_within_cache_window(self) -> None:
        publisher = FakePublisher()
        adapter = GoogleGmailAdapter(
            token_store=None,  # type: ignore[arg-type]
            scopes=(),
            email_publisher=publisher,
        )
        messages = {
            "message-1": IncomingEmail("message-1", "Sender <person@example.com>", "one"),
            "message-2": IncomingEmail("message-2", "person@example.com", "two"),
            "message-3": IncomingEmail("message-3", "other@example.com", "three"),
        }
        adapter.read_message = messages.__getitem__

        adapter._process_messages(list(messages))

        self.assertEqual(
            [email.email_id for email in publisher.emails], ["message-1", "message-3"]
        )

    def test_decodes_gmail_notification_and_reads_history(self) -> None:
        adapter = FakeGmailAdapter()
        notification = {"emailAddress": "user@example.com", "historyId": "12345"}
        envelope = {
            "message": {
                "data": base64.b64encode(json.dumps(notification).encode()).decode()
            }
        }

        result = adapter.handle(envelope)

        self.assertTrue(result.accepted)
        self.assertEqual(result.email_address, "user@example.com")
        self.assertEqual(result.history_id, "12345")
        self.assertEqual(result.message_ids, ["message-1"])
        self.assertEqual(adapter.history_ids, ["12344"])

    def test_rejects_missing_pubsub_data(self) -> None:
        with self.assertRaisesRegex(ValueError, "data is missing"):
            FakeGmailAdapter().handle({"message": {}})


if __name__ == "__main__":
    unittest.main()


class _FakeGmailService:
    def __init__(self, message: dict[str, object]) -> None:
        self._message = message

    def users(self) -> "_FakeGmailService":
        return self

    def messages(self) -> "_FakeGmailService":
        return self

    def get(self, **_: object) -> "_FakeGmailService":
        return self

    def execute(self) -> dict[str, object]:
        return self._message
