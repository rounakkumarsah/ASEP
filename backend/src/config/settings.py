"""
ASEP — Configuration & Settings
==================================
Single source of truth for all runtime configuration.

Uses Pydantic v2 BaseSettings with environment variable loading.
Values are resolved in this priority order:
  1. Environment variables (highest priority)
  2. .env file
  3. Field defaults

TODO (Phase 0.2):
    - Add secrets manager integration (AWS SSM / Vault / GCP Secret Manager)
    - Add config validation on startup (e.g. reachable URLs)
    - Split into domain-specific config classes (DBConfig, AIConfig, etc.)
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global application settings.

    All fields can be overridden via environment variables.
    Field names are matched case-insensitively by Pydantic.
    """

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -----------------------------------------------------------------------
    # Application
    # -----------------------------------------------------------------------
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_NAME: str = "ASEP"
    APP_VERSION: str = "0.1.0"
    APP_LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = Field(default=8000, ge=1, le=65535)
    APP_RELOAD: bool = True
    APP_WORKERS: int = Field(default=1, ge=1)

    # -----------------------------------------------------------------------
    # Security / Authentication
    # -----------------------------------------------------------------------
    SECRET_KEY: str = "change-this-to-a-random-256-bit-secret"
    JWT_SECRET_KEY: str = "change_me_in_production"
    JWT_REFRESH_SECRET_KEY: str = "change_me_in_production_refresh"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # Redis Settings
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching and distributed locks."
    )

    # Neo4j Settings
    NEO4J_URI: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    NEO4J_USER: str = Field(default="neo4j", description="Neo4j user")
    NEO4J_PASSWORD: str = Field(default="password", description="Neo4j password")
    NEO4J_DATABASE: str = Field(default="neo4j", description="Neo4j database name")

    # Qdrant Settings
    QDRANT_URL: str = Field(default="http://localhost:6333", description="Qdrant API URL")
    QDRANT_API_KEY: str | None = Field(default=None, description="Qdrant API Key")

    # Embedding Provider Settings
    EMBEDDING_API_URL: str = Field(
        default="http://localhost:11434/v1/embeddings", 
        description="OpenAI-compatible embedding endpoint URL"
    )
    EMBEDDING_API_KEY: str | None = Field(default=None, description="API Key for embedding service")
    EMBEDDING_MODEL: str = Field(default="nomic-embed-text", description="Name of the embedding model")

    # LLM Settings
    LLM_API_URL: str = Field(
        default="http://localhost:11434/v1/chat/completions",
        description="OpenAI-compatible chat completions endpoint URL"
    )
    LLM_API_KEY: str | None = Field(default=None, description="API Key for the LLM service")
    LLM_MODEL: str = Field(default="qwen2.5-coder:7b", description="Name of the LLM model to use")

    # -----------------------------------------------------------------------
    # PostgreSQL
    # -----------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://asep:changeme@localhost:5432/asep"

    # -----------------------------------------------------------------------
    # Redis
    # -----------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # -----------------------------------------------------------------------
    # Neo4j
    # -----------------------------------------------------------------------
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "changeme"

    # -----------------------------------------------------------------------
    # Qdrant
    # -----------------------------------------------------------------------
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = Field(default=6333, ge=1, le=65535)

    # -----------------------------------------------------------------------
    # Ollama
    # -----------------------------------------------------------------------
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3.2"

    # -----------------------------------------------------------------------
    # CORS
    # -----------------------------------------------------------------------
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Turnstile
    TURNSTILE_SECRET: str | None = None

    # SMTP / Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAIL_FROM: str = "noreply@asep.local"

    # -----------------------------------------------------------------------
    # Computed helpers
    # -----------------------------------------------------------------------
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @field_validator("SECRET_KEY", "JWT_SECRET_KEY", "JWT_REFRESH_SECRET_KEY")
    @classmethod
    def secret_key_must_not_be_default_in_production(cls, v: str, info: object) -> str:
        # Pydantic v2 field_validator behavior: info provides access to other parsed fields.
        # However, to access APP_ENV securely across all fields, it's safer to just check
        # if the value matches the known default defaults.
        defaults = [
            "change-this-to-a-random-256-bit-secret",
            "change_me_in_production",
            "change_me_in_production_refresh"
        ]
        
        import os
        is_prod = os.getenv("APP_ENV", "development") == "production"
        
        if is_prod and v in defaults:
            raise ValueError(f"CRITICAL: {info.field_name} must be properly configured in production environment.")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Using lru_cache means settings are loaded once per process lifetime,
    which is safe because environment variables don't change at runtime.
    """
    return Settings()
