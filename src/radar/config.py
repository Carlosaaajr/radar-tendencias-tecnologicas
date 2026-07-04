"""Application settings loaded from environment variables / .env (Princípio III)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    project_endpoint: str = ""
    model_deployment_name: str = "gpt-5-radar"

    cosmos_endpoint: str = ""
    cosmos_key: str = ""

    analysis_budget_seconds: float = 360.0
    max_analyses_per_day: int = 10

    radar_offline: bool = False

    openalex_mailto: str | None = None


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
