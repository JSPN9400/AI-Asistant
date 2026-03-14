from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "work_assistant.db"
DEFAULT_FILE_STORAGE_PATH = PROJECT_ROOT / "storage"


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.resolve().as_posix()}"


class Settings(BaseSettings):
    app_name: str = "Sikha Work Assistant"
    environment: str = Field(default="development", alias="APP_ENV")
    api_key: str = Field(default="replace-in-prod", alias="ASSISTANT_API_KEY")
    jwt_secret: str = Field(default="replace-me", alias="JWT_SECRET")
    database_url: str = Field(default=_sqlite_url(DEFAULT_DATABASE_PATH), alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    file_storage_path: str = Field(default=str(DEFAULT_FILE_STORAGE_PATH), alias="FILE_STORAGE_PATH")
    enable_cloud_reasoner: bool = Field(default=False, alias="ASSISTANT_ENABLE_CLOUD_REASONER")
    # When true, the backend can decide which provider to use per task
    enable_auto_llm_routing: bool = Field(default=True, alias="ASSISTANT_ENABLE_AUTO_LLM_ROUTING")
    # Default/global provider; still used when auto routing is off
    llm_provider: str = Field(default="ollama", alias="ASSISTANT_LLM_PROVIDER")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    ollama_model: str = Field(default="phi3", alias="OLLAMA_MODEL")
    ollama_host: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_HOST")

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
