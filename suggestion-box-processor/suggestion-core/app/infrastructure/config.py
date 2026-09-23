from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Automatically load a .env file if present during local development
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings() # type: ignore[call-arg]