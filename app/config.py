# app/config.py
"""
Centralized application configuration.

Rules:
- config must NOT import app.db (or anything that imports app.db),
  otherwise you create circular imports.
- app.db may import settings, but settings must stay independent.
"""

from __future__ import annotations

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Keep extra="ignore" so extra env vars don't crash the app
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ---------------------
    # App
    # ---------------------
    app_name: str = Field(default="TaskHub API", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_port: int = Field(default=8000, alias="APP_PORT")

    # env: "dev" | "test" | "prod" (used in your codebase)
    env: str = Field(default="dev", alias="ENV")

    # ---------------------
    # Database
    # ---------------------
    database_url: str = Field(
        default="postgresql+asyncpg://taskhub:taskhub_pass@localhost:5432/taskhub",
        alias="DATABASE_URL",
    )
    sql_echo: bool = Field(default=False, alias="SQL_ECHO")

    # ---------------------
    # JWT
    # ---------------------
    jwt_secret: str = Field(default="CHANGE_ME", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=15, alias="JWT_EXPIRE_MINUTES")
    jwt_refresh_days: int = Field(default=7, alias="JWT_REFRESH_DAYS")

    # ---------------------
    # Redis / Celery
    # ---------------------
    redis_broker: str = Field(default="redis://localhost:6379/0", alias="REDIS_BROKER")


@lru_cache
def get_settings() -> Settings:
    """Cached settings for the process lifetime."""
    return Settings()


settings = get_settings()
