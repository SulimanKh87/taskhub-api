# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
# BaseSettings automatically loads values from environment variables or .env files

class Settings(BaseSettings):
    # === Application Metadata ===
    app_name: str                              # e.g., "TaskHub API"
    app_env: str                               # e.g., "development", "production"
    app_debug: bool                            # Enables debug mode for FastAPI
    app_port: int                              # API port number (e.g., 8000)

    # === MongoDB Configuration ===
    mongodb_uri: str                           # Full MongoDB connection URI
    mongodb_db: str                            # Database name

    # === JWT Configuration ===
    jwt_secret: str                            # Secret key for signing JWTs
    jwt_algorithm: str                         # Algorithm (e.g., HS256)
    jwt_expire_minutes: int                    # Access token expiry (minutes)
    jwt_refresh_days: int                      # Refresh token expiry (days)

    # === Redis / Celery Configuration ===
    redis_broker: str                          # Redis URL for Celery tasks

    # Load settings from `.env` and ignore extras not defined here
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Instantiate global settings object
settings = Settings()
