from enum import StrEnum

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    DEV = "dev"
    PROD = "prod"
    TEST = "test"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "event_analytics_platform"
    app_env: AppEnv = AppEnv.DEV
    debug: bool = False

    # Logs
    log_level: LogLevel = LogLevel.INFO

    # Database
    db_user: str = "postgres"
    db_password: str = ""
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "database"

    # redis/valkey
    cache_url: str = "redis://cache:6380/0"
    stream_url: str = "redis://stream:6379/0"

    # Rate Limiting (requests per minute)
    rate_limit_enabled: bool = False
    rate_limit_free_rpm: int = 100
    rate_limit_pro_rpm: int = 1000
    rate_limit_enterprise_rpm: int = 10000
    rate_limit_no_auth_rpm: int = 10  # fallback without API key
    rate_limit_project_create_rpm: int = 5

    # Worker settings
    batch_size: int = 100
    read_timeout_ms: int = 1000

    # Security
    secret_token: str = ""

    @property
    def is_prod(self) -> bool:
        return self.app_env == AppEnv.PROD

    @property
    def is_rate_limit_enabled(self) -> bool:
        if self.app_env == AppEnv.TEST:
            return False
        return self.rate_limit_enabled

    @computed_field
    def db_dsn(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
