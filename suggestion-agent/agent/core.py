from collections.abc import Callable
from typing import Any

from google.protobuf.json_format import ParseDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from schemas import suggestion_pb2
from schemas.pydantic_schemas import SuggestionOutputSchema

from .config import AgentSettings
from .prompts import HUMAN_PROMPT_TEMPLATE, SYSTEM_INSTRUCTIONS


class SuggestionAgent:
    def __init__(
        self,
        settings: AgentSettings | None = None,
        model_factory: Callable[..., Any] = ChatOpenAI,
    ) -> None:
        resolved_settings = settings or AgentSettings()
        if not resolved_settings.model_api_key:
            raise ValueError("MODEL_API_KEY is required")
        if resolved_settings.model_provider == "gemini":
            model = ChatGoogleGenerativeAI(
                model=resolved_settings.model_name,
                temperature=resolved_settings.temperature,
                google_api_key=resolved_settings.model_api_key,
            )
        elif resolved_settings.model_provider == "openai":
            model = model_factory(
                model=resolved_settings.model_name,
                temperature=resolved_settings.temperature,
                api_key=resolved_settings.model_api_key,
            )
        else:
            raise ValueError(f"Unsupported MODEL_PROVIDER: {resolved_settings.model_provider}")
        structured_model = model.with_structured_output(SuggestionOutputSchema)
        prompt = ChatPromptTemplate.from_messages(
            [("system", SYSTEM_INSTRUCTIONS), ("human", HUMAN_PROMPT_TEMPLATE)]
        )
        self._chain = prompt | structured_model

    def process(
        self,
        email_id: str,
        sender_email: str,
        email_body: str,
    ) -> suggestion_pb2.SuggestionAnalysis:
        result = self._chain.invoke(
            {
                "sender_email": sender_email,
                "email_body": email_body,
            }
        )
        if isinstance(result, SuggestionOutputSchema):
            result_data = result.model_dump(mode="json")
        elif isinstance(result, dict):
            result_data = result
        else:
            raise TypeError("The structured model returned an unsupported result")

        result_data["email_id"] = email_id
        analysis = suggestion_pb2.SuggestionAnalysis()
        ParseDict(result_data, analysis)
        analysis.original_message.CopyFrom(
            suggestion_pb2.EmailMessage(
                email_id=email_id,
                sender_email=sender_email,
                body=email_body,
            )
        )
        return analysis
