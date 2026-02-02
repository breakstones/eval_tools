"""Application configuration module."""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings.

    Default ports (see PORTS.config in project root):
    - Backend: 8001
    - Frontend: 5173
    """

    # Application
    APP_NAME: str = "LLM Eval Studio"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./llm_eval.db?check_same_thread=false"

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:5173", "http://localhost:3000"])

    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set[str] = Field(default={".xlsx", ".xls"})

    # Evaluation
    MAX_CONCURRENT_REQUESTS: int = 5
    REQUEST_TIMEOUT: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
