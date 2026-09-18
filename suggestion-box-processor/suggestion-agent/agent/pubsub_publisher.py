import logging

from google.cloud import pubsub_v1

from schemas.v1 import suggestion_pb2

logger = logging.getLogger(__name__)


class SuggestionPublisher:
    def __init__(self, topic_name: str) -> None:
        self._publisher: pubsub_v1.PublisherClient | None = None
        self._topic_name = topic_name

    def publish(self, analysis: suggestion_pb2.SuggestionAnalysis) -> None:
        if self._publisher is None:
            self._publisher = pubsub_v1.PublisherClient()
        message_id = self._publisher.publish(
            self._topic_name,
            analysis.SerializeToString(),
        ).result()
        logger.info(
            "Published SuggestionAnalysis email_id=%s topic=%s pubsub_message_id=%s",
            analysis.email_id,
            self._topic_name,
            message_id,
        )
