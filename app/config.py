"""
Centralized application configuration.

All values can be overridden via environment variables or a `.env` file
(see `.env.example`). Falling back to sensible local-dev defaults keeps
`pip install -r requirements.txt && uvicorn app.main:app` working with
zero setup, while Docker/production deployments override via env vars.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "TaskFlow API"
    environment: str = "development"

    # Database
    # Defaults to a local SQLite file so the project runs with no external
    # services. docker-compose.yml overrides this to point at Postgres.
    database_url: str = "sqlite:///./taskflow.db"

    # Auth / JWT
    secret_key: str = "CHANGE_ME_IN_PRODUCTION_use_openssl_rand_-hex_32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Rate limiting
    rate_limit_auth: str = "5/minute"
    rate_limit_default: str = "100/minute"


settings = Settings()
