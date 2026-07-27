from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "DownloadWebService"
    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://dws:dws_secret@localhost:5432/dws"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "amqp://dws:dws_secret@localhost:5672//"
    celery_result_backend: str = "redis://localhost:6379/1"

    external_api_base_url: str = "https://example.com"
    x_candidate_id: str = "local-dev-candidate"
    external_api_timeout_seconds: float = 30.0
    external_api_max_attempts: int = 5
    files_storage_path: str = "./data/files"


@lru_cache
def get_settings() -> Settings:
    return Settings()
