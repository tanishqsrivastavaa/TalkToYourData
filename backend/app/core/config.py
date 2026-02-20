"""Core configuration module — reads settings from environment / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    app_env: str = "development"
    app_debug: bool = True
    app_port: int = 8000

    # ── Database ─────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/dbname"

    # ── Redis ────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Auth / Security ──────────────────────────────────────────
    secret_key: str = "change-me-to-a-random-string"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    # ── OpenAI ───────────────────────────────────────────────────
    openai_api_key: str = ""

    # ── Deepgram ─────────────────────────────────────────────────
    deepgram_api_key: str = ""

    # ── LiveKit ──────────────────────────────────────────────────
    livekit_url: str = "ws://localhost:7880"
    livekit_api_key: str = "devkey"
    livekit_api_secret: str = "secret"

    # ── Model names ──────────────────────────────────────────────
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"


settings = Settings()
