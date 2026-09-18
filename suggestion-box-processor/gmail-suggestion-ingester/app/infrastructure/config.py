import json
import os
from dataclasses import dataclass
from typing import cast 
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    client_secret_json: str
    redirect_uri: str
    token_json: str | None
    maintenance_username: str
    maintenance_password: str
    scopes: tuple[str, ...]
    pubsub_topic: str | None
    duplicate_sender_ttl_seconds: int
    ignored_gmail_labels: tuple[str, ...]

    # Automatically load a .env file if present during local development
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings() # type: ignore[call-arg]