from fastapi.security import HTTPBasic

from app.infrastructure.config import settings
from app.infrastructure.pubsub_publisher import PubSubEmailPublisher
from app.infrastructure.auth.token_store import InMemoryTokenStore
from app.infrastructure.gmail.google_oauth_adapter import GoogleOAuthAdapter
from app.infrastructure.gmail.google_gmail_adapter import GoogleGmailAdapter
from app.infrastructure.auth.basic_credentials_store import BasicCredentialsStore


gmail_adapter  = None
oauth_adapter = None

def get_credentials_store() -> BasicCredentialsStore:   
    return BasicCredentialsStore()

def get_credentials_provider() -> HTTPBasic:
    return HTTPBasic()

def get_token_store() -> InMemoryTokenStore:
    return InMemoryTokenStore()

def get_oauth_adapter():
    global oauth_adapter
    if oauth_adapter is None:
        oauth_adapter = GoogleOAuthAdapter(
            client_secret_json=settings.client_secret_json,
            scopes=("https://www.googleapis.com/auth/gmail.readonly",),
            redirect_uri=settings.redirect_uri,
            token_store=get_token_store(),
        )
    return oauth_adapter

def get_gmail_adapter():
    global gmail_adapter
    if gmail_adapter is None:
        gmail_adapter = GoogleGmailAdapter(get_oauth_adapter())
    return gmail_adapter

def get_pubsub_email_publisher():
    if not settings.pubsub_topic:
        raise RuntimeError("PUBSUB_TOPIC is required")
    return PubSubEmailPublisher(settings.core_topic)



