from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sikha Work Assistant"
    environment: str = Field(default="development", alias="APP_ENV")
    api_key: str = Field(default="replace-in-prod", alias="ASSISTANT_API_KEY")
    jwt_secret: str = Field(default="replace-me", alias="JWT_SECRET")
    database_url: str = Field(default="sqlite:///./work_assistant.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    file_storage_path: str = Field(default="./storage", alias="FILE_STORAGE_PATH")
    enable_cloud_reasoner: bool = Field(default=False, alias="ASSISTANT_ENABLE_CLOUD_REASONER")
    llm_provider: str = Field(default="gemini", alias="ASSISTANT_LLM_PROVIDER")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    ollama_model: str = Field(default="phi3", alias="OLLAMA_MODEL")
    ollama_host: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_HOST")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
