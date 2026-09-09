import json
import os
from dataclasses import dataclass
from typing import cast


@dataclass(frozen=True)
class Settings:
    client_secret_json: str
    redirect_uri: str
    token_json: str | None
    maintenance_username: str
    maintenance_password: str
    scopes: tuple[str, ...]
    pubsub_topic: str | None
    google_cloud_project: str | None
    suggestion_agent_url: str
    suggestion_agent_topic: str
    duplicate_sender_ttl_seconds: int
    ignored_gmail_labels: tuple[str, ...]

    @classmethod
    def from_environment(cls) -> "Settings":
        client_secret_json = os.getenv("GOOGLE_CLIENT_SECRET_JSON")
        if not client_secret_json:
            raise RuntimeError("GOOGLE_CLIENT_SECRET_JSON environment variable is missing")

        try:
            json.loads(client_secret_json)
        except json.JSONDecodeError as error:
            raise RuntimeError("GOOGLE_CLIENT_SECRET_JSON is not valid JSON") from error

        return cls(
            client_secret_json=client_secret_json,
            redirect_uri=cast(str, os.getenv("GOOGLE_REDIRECT_URI")),
            token_json=os.getenv("GMAIL_TOKEN_JSON"),
            maintenance_username=os.getenv("MAINTENANCE_USERNAME", "maintenance"),
            maintenance_password=_required_environment("MAINTENANCE_PASSWORD"),
            scopes=("https://www.googleapis.com/auth/gmail.readonly",),
            pubsub_topic=os.getenv("GOOGLE_PUBSUB_TOPIC"),
            google_cloud_project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            suggestion_agent_url=os.getenv(
                "SUGGESTION_AGENT_URL", "http://localhost:8090"
            ),
            suggestion_agent_topic=os.getenv(
                "SUGGESTION_AGENT_TOPIC",
                "projects/suggestion-box-508020/topics/analysis-request",
            ),
            duplicate_sender_ttl_seconds=int(
                os.getenv("DUPLICATE_SENDER_TTL_SECONDS", "60")
            ),
            ignored_gmail_labels=tuple(
                label.strip().upper()
                for label in os.getenv(
                    "IGNORED_GMAIL_LABELS",
                    "SPAM,TRASH,SENT,CATEGORY_PROMOTIONS,CATEGORY_SOCIAL,CATEGORY_UPDATES,CATEGORY_FORUMS",
                ).split(",")
                if label.strip()
            ),
        )


def _required_environment(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is missing")
    return value
