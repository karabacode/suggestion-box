import logging

from google.cloud import pubsub_v1
from app.schemas.v1 import submit_suggestion_dto_pb2
from app.schemas.v1.submit_suggestion_dto_p2p import SubmitSuggestionDto

logger = logging.getLogger(__name__)


class PubSubEmailPublisher:

    def __init__(self, topic_name: str) -> None:
        logger.info("Initializing PubSubEmailPublisher")
        self._publisher = pubsub_v1.PublisherClient()
        self._topic_name = topic_name

    def publish(self, submitSuggestionDto: SubmitSuggestionDto) -> None:
        logger.info(f"Publishing submit suggestion DTO: {submitSuggestionDto}")
        # Dynamically fetch message class from the module descriptor
        message = submit_suggestion_dto_pb2.SubmitSuggestionDto(
            sender = submitSuggestionDto.sender,
            body = submitSuggestionDto.body,
            external_reference = submitSuggestionDto.external_reference,
        )
        logger.info(f"Constructed PubSub message: {message.SerializeToString()}")
        publish_future = self._publisher.publish(
            self._topic_name, message.SerializeToString()
        )
        message_id = publish_future.result()
        logger.info(
            "Published SubmitSuggestionDto message_id=%s topic=%s pubsub_message_id=%s",
            submitSuggestionDto.external_reference,
            self._topic_name,
            message_id,
        )