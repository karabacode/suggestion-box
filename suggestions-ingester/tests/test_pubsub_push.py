import base64
import json
import unittest

from app.infrastructure.gmail.google_gmail import GoogleGmailAdapter


class FakeGmailAdapter(GoogleGmailAdapter):
    def __init__(self) -> None:
        self.history_ids: list[str] = []
        self._email_publisher = None
        self._history_cursor = None

    def list_history(self, history_id: str) -> list[str]:
        self.history_ids.append(history_id)
        return ["message-1"]


class PubSubPushTests(unittest.TestCase):
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
