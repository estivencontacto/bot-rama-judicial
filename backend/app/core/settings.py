"""Configuracion centralizada de la aplicacion.

Todas las variables sensibles o dependientes del ambiente se leen desde `.env`.
El cache evita recrear settings en cada request.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables de entorno tipadas para backend, scraper, seguridad y Telegram."""

    app_name: str = "Bot Rama Judicial API"
    environment: str = "local"
    debug: bool = False

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/bot_rama_judicial"
    )
    redis_url: str | None = None
    queue_name: str = "scraper_jobs"
    secret_key: str = Field(default="change-me-in-production")
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14
    max_failed_login_attempts: int = 5
    login_lock_minutes: int = 15
    algorithm: str = "HS256"

    frontend_origin: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    rama_judicial_url: str = (
        "https://consultaprocesos.ramajudicial.gov.co/Procesos/NumeroRadicacion"
    )
    selenium_browser: str = "edge"
    selenium_headless: bool = True
    selenium_timeout_seconds: int = 20
    scraper_max_retries: int = 3
    scraper_retry_delay_seconds: float = 2.0

    telegram_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_max_chars: int = 4000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins(self) -> List[AnyHttpUrl | str]:
        """Convierte la lista de origenes CORS en una estructura consumible por FastAPI."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Entrega una instancia cacheada de settings para toda la aplicacion."""
    return Settings()
