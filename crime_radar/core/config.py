"""Core configuration and settings."""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Crime Radar"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, validation_alias="DEBUG")

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/crime_radar",
        validation_alias="DATABASE_URL",
    )

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL",
    )

    secret_key: str = Field(
        default="change-me-in-production",
        validation_alias="SECRET_KEY",
    )

    data_dir: Path = Field(default=Path("./data"))

    risk_update_interval: int = 300  # seconds
    pattern_detection_threshold: float = 0.7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
