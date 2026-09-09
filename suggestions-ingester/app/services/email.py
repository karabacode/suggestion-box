from dataclasses import dataclass


@dataclass(frozen=True)
class IncomingEmail:
    email_id: str
    sender_email: str
    body: str
