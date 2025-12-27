# app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ------------------------------------------------------------
    # Application Metadata
    # ------------------------------------------------------------
    app_name: str
    app_env: str
    app_debug: bool
    app_port: int

    # ------------------------------------------------------------
    # Database (PostgreSQL)
    # ------------------------------------------------------------
    database_url: str  # postgresql+asyncpg://user:pass@host:5432/db

    # ------------------------------------------------------------
    # JWT Configuration
    # ------------------------------------------------------------
    jwt_secret: str
    jwt_algorithm: str
    jwt_expire_minutes: int
    jwt_refresh_days: int

    # ------------------------------------------------------------
    # Redis / Celery
    # ------------------------------------------------------------
    redis_broker: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
