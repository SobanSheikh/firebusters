from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = (
        "postgresql+asyncpg://firebusters:firebusters_dev@localhost:5434/firebusters"
    )
    cors_origins: str = "http://localhost:5173"
    supabase_url: str | None = None
    supabase_publishable_key: str | None = None
    supabase_secret_key: str | None = None
    supabase_storage_bucket: str = "firebusters-assets"
    ai_provider: Literal["groq", "gemini", "openai", "anthropic"] = "groq"
    ai_model: str = "llama-3.3-70b-versatile"
    ai_base_url: str | None = None
    ai_timeout_seconds: float = 30.0
    ai_max_output_tokens: int = 2048
    groq_api_key: str | None = None
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    r2_endpoint: str | None = None
    r2_bucket: str = "flamelens-assets"
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_public_base_url: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def ai_api_key(self) -> str | None:
        """Return the credential configured for the selected provider."""
        return {
            "groq": self.groq_api_key,
            "gemini": self.gemini_api_key,
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }[self.ai_provider]

    @property
    def resolved_ai_base_url(self) -> str | None:
        """Resolve compatible endpoints while allowing an explicit override."""
        if self.ai_base_url:
            return self.ai_base_url
        if self.ai_provider == "groq":
            return "https://api.groq.com/openai/v1"
        if self.ai_provider == "gemini":
            return "https://generativelanguage.googleapis.com/v1beta/openai/"
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
