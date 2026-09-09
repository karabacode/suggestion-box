from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_provider: str = "gemini"
    model_api_key: str | None = None
    model_name: str = "gemini-3.6-flash"
    temperature: float = 0.1
    output_topic: str = "projects/suggestion-box-508020/topics/suggestion-analysis"
