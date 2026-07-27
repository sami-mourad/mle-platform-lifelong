from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    log_level: str = "INFO"
    data_dir: Path = Path(".data")
    artifact_dir: Path = Path(".artifacts")
    model_refresh_seconds: int = Field(default=5, ge=1)

    mlflow_tracking_uri: str | None = None
    mlflow_experiment_name: str = "dummy-imbalance"
    mlflow_register_models: bool = False
    mlflow_model_name: str = "dummy_imbalance_risk"

    redis_url: str = "redis://localhost:6379/0"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    allow_dev_force_fallback: bool = True

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
