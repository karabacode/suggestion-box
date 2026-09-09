from pydantic import BaseModel, Field


class VibeAnalysisSchema(BaseModel):
    primary_vibe: str = Field(
        description="The dominant emotional tone, such as frustrated, enthusiastic, skeptical, or constructive."
    )
    urgency_level: str = Field(
        description="How urgently the sender needs action: low, medium, high, or critical."
    )
    communication_style: str = Field(
        description="The sender's communication style, such as direct, casual, formal, or demanding."
    )
    tags: list[str] = Field(
        description="Behavioral and product-context tags, such as churn_risk, power_user, or ui_feedback."
    )


class SuggestionOutputSchema(BaseModel):
    email_id: str = Field(description="The source email identifier supplied by the ingester.")
    sender_name: str = Field(description="The sender's display name, if available from the email context.")
    sender_email: str = Field(description="The sender's email address.")
    category: str = Field(
        description="The primary suggestion category, such as feature_request, ui_ux, pricing, or bug_report."
    )
    suggested_action: str = Field(
        description="A concise, actionable summary of the feature suggestion or requested change."
    )
    vibe: VibeAnalysisSchema = Field(
        description="Qualitative analysis of the sender's emotional tone, urgency, style, and behavioral signals."
    )
    draft_reply: str = Field(
        description="A polite reply draft matched to the sender's tone and acknowledging the suggestion."
    )
    timestamp: int = Field(description="Unix timestamp in seconds when the analysis was produced.")
