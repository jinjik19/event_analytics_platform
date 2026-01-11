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

    # Logs
    log_level: LogLevel = LogLevel.INFO

    # Database
    db_user: str = "postgres"
    db_password: str = ""
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "database"

    # broker
    broker_url: str = "redis://localhost:6379/0"

    @property
    def is_prod(self) -> bool:
        return self.app_env == AppEnv.PROD

    @computed_field
    def db_dsn(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
