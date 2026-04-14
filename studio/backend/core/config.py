from functools import lru_cache

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: AnyHttpUrl | None = None
    supabase_service_key: str | None = None
    supabase_anon_key: str | None = None
    secret_key: str | None = None
    admin_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    database_url: str
    redis_url: str
    vector_store_path: str = "./data/faiss_index"
    frontend_url: AnyHttpUrl | None = None
    log_level: str = "INFO"
    celery_queue_name: str = "studio_tasks"
    celery_task_time_limit: int = 600
    celery_task_soft_time_limit: int = 540
    celery_task_max_retries: int = 3
    celery_retry_base_delay_seconds: int = 5
    stream_keepalive_timeout_seconds: int = 20
    event_store_ttl_seconds: int = 3600
    request_timeout_seconds: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def async_database_url(self) -> str:
        if self.database_url.startswith("postgresql+asyncpg://"):
            return self.database_url
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace(
                "postgresql://",
                "postgresql+asyncpg://",
                1,
            )
        return self.database_url

    @property
    def sync_database_url(self) -> str:
        if self.database_url.startswith("postgresql+asyncpg://"):
            return self.database_url.replace(
                "postgresql+asyncpg://",
                "postgresql+psycopg2://",
                1,
            )
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace(
                "postgresql://",
                "postgresql+psycopg2://",
                1,
            )
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
