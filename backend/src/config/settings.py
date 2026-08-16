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

    # -----------------------------------------------------------------------
    # Redis
    # -----------------------------------------------------------------------
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL. Use rediss:// for TLS (production)."
    )
    REDIS_TERMINAL_CHANNEL_PREFIX: str = Field(
        default="opensep:terminal",
        description="Prefix channel key for PTY WebSocket routing broadcasts."
    )
    REDIS_PASSWORD: str | None = Field(
        default=None,
        description="Optional password for Redis authentication."
    )
    
    # -----------------------------------------------------------------------
    # Terminal & Governance
    # -----------------------------------------------------------------------
    TERMINAL_SHELL: str = Field(
        default="/bin/bash",
        description="Default shell path for interactive PTY allocations."
    )
    OPA_ENABLED: bool = Field(
        default=False,
        description="Enforces Open Policy Agent pre-execution command checks."
    )
    OPA_URL: str = Field(
        default="http://localhost:8181/v1/data/asep/policy",
        description="OPA endpoint URL."
    )
    # -----------------------------------------------------------------------
    # AI Providers Configuration Keys
    # -----------------------------------------------------------------------
    ANTHROPIC_API_KEY: str | None = Field(
        default=None,
        description="API Key for Anthropic Claude LLM provider."
    )

    # -----------------------------------------------------------------------

    # Qdrant
    # -----------------------------------------------------------------------
    QDRANT_URL: str = Field(
        default="http://localhost:6333",
        description="Qdrant REST API URL. Use the Qdrant Cloud cluster URL for production.",
    )
    QDRANT_API_KEY: str | None = Field(
        default=None,
        description="Qdrant API key. Required for Qdrant Cloud.",
    )
    QDRANT_COLLECTION: str = Field(
        default="asep_documents",
        description="Default Qdrant collection name for document vectors.",
    )
    QDRANT_VECTOR_SIZE: int = Field(
        default=1536,
        description="Embedding vector dimension. Must match the embedding model output size.",
    )

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

    # Gemini AI
    GEMINI_API_KEY: str | None = Field(default=None, description="Google AI Studio Gemini API key")

    # -----------------------------------------------------------------------
    # PostgreSQL
    # -----------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://asep:changeme@localhost:5432/asep"


    # -----------------------------------------------------------------------
    # Neo4j
    # -----------------------------------------------------------------------
    NEO4J_URI: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    NEO4J_USER: str = Field(default="neo4j", validation_alias="NEO4J_USERNAME", description="Neo4j username")
    NEO4J_PASSWORD: str = Field(default="changeme", description="Neo4j password")
    NEO4J_DATABASE: str | None = Field(default=None, description="Neo4j database name (None = driver default, use None for Aura)")

    # -----------------------------------------------------------------------
    # Qdrant
    # -----------------------------------------------------------------------
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = Field(default=6333, ge=1, le=65535)
    # Note: QDRANT_URL and QDRANT_API_KEY are defined above in the primary Qdrant block.
    # QDRANT_HOST / QDRANT_PORT are retained for Docker-internal routing compatibility.

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
    ENABLE_TURNSTILE: bool = False
    TURNSTILE_SECRET_KEY: str | None = None
    TURNSTILE_SECRET: str | None = None

    @property
    def turnstile_secret(self) -> str | None:
        """Return TURNSTILE_SECRET_KEY or TURNSTILE_SECRET fallback."""
        return self.TURNSTILE_SECRET_KEY or self.TURNSTILE_SECRET

    # SMTP / Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAIL_FROM: str = "noreply@asep.local"
    RESEND_API_KEY: str | None = Field(default=None, description="Resend API Key for production emails")
    FRONTEND_URL: str = Field(default="http://localhost:3000", description="Frontend URL for email links")

    # -----------------------------------------------------------------------
    # Razorpay
    # -----------------------------------------------------------------------
    RAZORPAY_KEY_ID: str | None = Field(
        default=None,
        description="Razorpay Key ID (rzp_test_* for test mode, rzp_live_* for live mode).",
    )
    RAZORPAY_KEY_SECRET: str | None = Field(
        default=None,
        description="Razorpay Key Secret — NEVER expose to frontend.",
    )
    RAZORPAY_WEBHOOK_SECRET: str | None = Field(
        default=None,
        description="Razorpay Webhook Secret for verifying webhook signatures.",
    )

    # -----------------------------------------------------------------------
    # GitHub OAuth
    # -----------------------------------------------------------------------
    GITHUB_CLIENT_ID: str | None = Field(
        default=None,
        description="GitHub OAuth App Client ID.",
    )
    GITHUB_CLIENT_SECRET: str | None = Field(
        default=None,
        description="GitHub OAuth App Client Secret — NEVER expose to frontend.",
    )
    GITHUB_REDIRECT_URI: str = Field(
        default="http://localhost:8000/api/v1/auth/oauth/github/callback",
        description="GitHub OAuth callback URI (must match GitHub App settings).",
    )

    # -----------------------------------------------------------------------
    # Google OAuth
    # -----------------------------------------------------------------------
    GOOGLE_CLIENT_ID: str | None = Field(
        default=None,
        description="Google OAuth 2.0 Client ID.",
    )
    GOOGLE_CLIENT_SECRET: str | None = Field(
        default=None,
        description="Google OAuth 2.0 Client Secret — NEVER expose to frontend.",
    )
    GOOGLE_REDIRECT_URI: str = Field(
        default="http://localhost:8000/api/v1/auth/oauth/google/callback",
        description="Google OAuth callback URI (must match Google Cloud Console settings).",
    )

    # -----------------------------------------------------------------------
    # Frontend
    # -----------------------------------------------------------------------
    FRONTEND_OAUTH_CALLBACK_URL: str = Field(
        default="http://localhost:3000/auth/callback",
        description="Frontend URL that the backend redirects to after OAuth callback.",
    )
    SENTRY_DSN_BACKEND: str | None = Field(
        default="https://5c21de97f08fe501ade2875fc00e3678@o4511818217226240.ingest.us.sentry.io/4511818269065216",
        description="Sentry DSN for backend error tracking.",
    )
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001,https://asep-ai.vercel.app",
        description="Comma-separated list of allowed CORS origins.",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list. Rejects wildcards in production."""
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        if self.APP_ENV == "production" and "*" in origins:
            raise ValueError("Wildcard CORS origins are forbidden in production when credentials are allowed.")
        if self.APP_ENV == "development":
            # Allow common local network IPs (e.g. 172.x.x.x, 192.168.x.x, 10.x.x.x) during dev
            origins.extend([
                "http://172.22.160.1:3000", "http://172.22.160.1:3001",
                "http://192.168.1.1:3000", "http://192.168.1.1:3001"
            ])
        return list(set(origins))

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        import os
        is_prod = os.getenv("APP_ENV", "development") == "production"
        
        # Enforce that in production a production-grade database URL is provided
        default_indicators = ["localhost", "postgres:5432", "changeme", "asep:changeme"]
        if is_prod and any(ind in v for ind in default_indicators):
            raise ValueError(
                "CRITICAL: A production DATABASE_URL environment variable is required when APP_ENV=production. "
                "Local fallback database credentials are not permitted in production."
            )
            
        # Standardize connection scheme to AsyncPG or Psycopg async engine format
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            
        # Strip query parameters like sslmode=require that asyncpg rejects as unsupported kwargs
        if "?" in v:
            v = v.split("?")[0]
        return v

    @field_validator("QDRANT_URL")
    @classmethod
    def validate_qdrant_url(cls, v: str) -> str:
        v = v.rstrip("/")
        # Qdrant Cloud HTTPS endpoints run on port 443 (HTTPS REST) or 6334 (gRPC).
        # Appending port :6333 to an https:// cloud cluster URL results in 404 page not found.
        if v.startswith("https://") and ":6333" in v:
            v = v.replace(":6333", "")
        return v

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

    @field_validator("GEMINI_API_KEY", "REDIS_URL")
    @classmethod
    def validate_production_services(cls, v: str | None, info: object) -> str | None:
        import os
        is_prod = os.getenv("APP_ENV", "development") == "production"
        if is_prod and not v:
            raise ValueError(f"CRITICAL: {info.field_name} must be explicitly configured when APP_ENV=production.")
        return v


        
from pydantic import model_validator
from typing import Any

# Re-declare Settings class suffix with root validators
class Settings(Settings):
    @model_validator(mode="after")
    def validate_production_environment_variables(self) -> Settings:
        import os
        app_env = os.getenv("APP_ENV", "development")
        is_production_like = app_env in ("staging", "production") or self.APP_ENV in ("staging", "production")
        
        if is_production_like:
            # 1. Validate DATABASE_URL
            db_url = getattr(self, "DATABASE_URL", "") or os.getenv("DATABASE_URL", "")
            db_fallbacks = ["localhost", "postgres:5432", "changeme", "asep:changeme"]
            if not db_url or any(fb in db_url for fb in db_fallbacks):
                raise ValueError(f"CRITICAL: Production DATABASE_URL must not use local fallbacks: {db_url}")
                
            # 2. Validate REDIS_URL
            redis_url = getattr(self, "REDIS_URL", "") or os.getenv("REDIS_URL", "")
            redis_fallbacks = ["localhost", "redis:6379", "127.0.0.1"]
            if not redis_url or any(fb in redis_url for fb in redis_fallbacks):
                raise ValueError(f"CRITICAL: Production REDIS_URL must not use local fallbacks: {redis_url}")
                
            # 3. Validate SECRET_KEY keys
            secret_key = getattr(self, "SECRET_KEY", "")
            secret_fallbacks = ["change-this-to-a-random-256-bit-secret", "change_me_in_production"]
            if not secret_key or any(fb in secret_key for fb in secret_fallbacks):
                raise ValueError(f"CRITICAL: Production SECRET_KEY must be properly configured.")
                
            # 4. Validate ANTHROPIC_API_KEY
            anthropic_key = getattr(self, "ANTHROPIC_API_KEY", "") or os.getenv("ANTHROPIC_API_KEY", "")
            if not anthropic_key:
                raise ValueError("CRITICAL: Production ANTHROPIC_API_KEY must be explicitly configured.")
                
        return self

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    """
    return Settings()
