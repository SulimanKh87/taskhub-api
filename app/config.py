# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str
    app_env: str
    app_debug: bool
    app_port: int

    mongodb_uri: str
    mongodb_db: str

    jwt_secret: str
    jwt_algorithm: str
    jwt_expire_minutes: int
    jwt_refresh_days: int

    redis_broker: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
