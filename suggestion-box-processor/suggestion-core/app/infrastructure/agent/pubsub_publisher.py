import logging

from google.cloud import pubsub_v1

from app.services.agent import EmailPublisher
from app.services.email import IncomingEmail
from schemas.v1 import suggestion_pb2

logger = logging.getLogger(__name__)


class GooglePubSubEmailPublisher(EmailPublisher):
    def __init__(self, topic_name: str) -> None:
        self._publisher = pubsub_v1.PublisherClient()
        self._topic_name = topic_name

    def publish(self, email: IncomingEmail) -> None:
        message = suggestion_pb2.EmailMessage(
            email_id=email.email_id,
            sender_email=email.sender_email,
            body=email.body,
        )
        publish_future = self._publisher.publish(
            self._topic_name, message.SerializeToString()
        )
        message_id = publish_future.result()
        logger.info(
            "Published EmailMessage email_id=%s topic=%s pubsub_message_id=%s",
            email.email_id,
            self._topic_name,
            message_id,
        )