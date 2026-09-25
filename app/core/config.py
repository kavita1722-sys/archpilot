"""Application configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import List, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    PROJECT_NAME: str = "ArchPilot"
    VERSION: str = "0.1.0"
    ENV: Literal["development", "production", "testing"] = "development"
    LOG_LEVEL: str = "INFO"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./archpilot.db"

    # LLM Provider Configuration
    LLM_PROVIDER: Literal["mock", "ollama", "openai_compatible"] = "mock"

    # Ollama Provider Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"

    # OpenAI-compatible Provider Settings
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Bounded Execution & Guardrails
    MAX_TASK_LENGTH: int = 4000
    MAX_STEPS: int = 6
    MAX_TOOL_RETRIES: int = 2
    MAX_VALIDATION_RETRIES: int = 2
    MAX_ITERATIONS: int = 12

    # Tool Execution Allowlist
    ALLOWED_TOOLS: List[str] = Field(
        default_factory=lambda: ["calculator", "web_search", "url_fetch"]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached instance of application settings."""
    return Settings()
