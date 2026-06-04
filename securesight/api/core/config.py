from __future__ import annotations

import functools
from pathlib import Path
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["development", "testing", "staging", "production"]


class MLWeights(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)

    isolation_forest: float = 0.35
    arima: float = 0.20
    prophet: float = 0.20
    zscore: float = 0.15
    ema: float = 0.10

    @field_validator("*", mode="after")
    @classmethod
    def _check_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("ML weight must be non-negative")
        return value

    def as_dict(self) -> dict[str, float]:
        return self.model_dump()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "SecureSight"
    app_version: str = "1.0.0"
    app_env: AppEnv = "development"
    debug: bool = False
    docs_enabled: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    api_reload: bool = False
    api_prefix: str = "/api/v1"
    api_request_timeout_seconds: int = 30

    secret_key: str = "change-me-in-production-please-32-chars-min"
    jwt_algorithm: str = "RS256"
    jwt_issuer: str = "securesight"
    jwt_audience: str = "securesight-api"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    jwt_private_key_path: Optional[Path] = None
    jwt_public_key_path: Optional[Path] = None
    jwt_algorithm_fallback: str = "HS256"
    bcrypt_rounds: int = 12

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/securesight"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout_seconds: int = 30
    database_echo: bool = False
    database_pool_pre_ping: bool = True

    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50
    redis_socket_timeout_seconds: float = 5.0
    redis_health_check_interval_seconds: int = 30

    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
        ]
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: List[str] = Field(default_factory=lambda: ["*"])

    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 20
    rate_limit_storage: Literal["memory", "redis"] = "memory"

    trusted_hosts: List[str] = Field(default_factory=lambda: ["*"])

    log_level: str = "INFO"
    log_json: bool = False
    log_file: Optional[Path] = None
    log_include_request_id: bool = True

    ml_weights: MLWeights = Field(default_factory=MLWeights)
    ml_min_train_samples: int = 30
    ml_ensemble_method: Literal["weighted_average", "voting", "max"] = "weighted_average"
    ml_retrain_interval_hours: int = 24

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_always_eager: bool = False
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_timezone: str = "UTC"

    sentry_dsn: Optional[str] = None
    sentry_environment: Optional[str] = None
    sentry_traces_sample_rate: float = 0.1

    @field_validator("cors_origins", "trusted_hosts", mode="before")
    @classmethod
    def _split_csv(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("cors_origins")
    @classmethod
    def _validate_cors(cls, value: List[str]) -> List[str]:
        cleaned = [origin.strip() for origin in value if origin and origin.strip()]
        for origin in cleaned:
            if origin != "*" and not origin.startswith(("http://", "https://")):
                raise ValueError(
                    f"CORS origin must start with http:// or https:// (got {origin!r})"
                )
        return cleaned

    @field_validator("api_port", "api_workers", "bcrypt_rounds", "rate_limit_per_minute")
    @classmethod
    def _validate_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("value must be positive")
        return value

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if normalized not in valid:
            raise ValueError(f"log_level must be one of {sorted(valid)}")
        return normalized

    @model_validator(mode="after")
    def _apply_env_defaults(self) -> "Settings":
        if self.app_env == "production":
            object.__setattr__(self, "log_json", True)
            object.__setattr__(self, "debug", False)
            object.__setattr__(self, "docs_enabled", False)
            if self.secret_key.startswith("change-me"):
                raise ValueError("secret_key must be overridden in production")
        if self.app_env == "development" and self.log_json is False and self.log_file is None:
            pass
        return self

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_testing(self) -> bool:
        return self.app_env == "testing"

    @property
    def is_staging(self) -> bool:
        return self.app_env == "staging"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def ml_weights_sum(self) -> float:
        return float(sum(self.ml_weights.as_dict().values()))

    @property
    def jwt_private_key(self) -> Optional[str]:
        if self.jwt_private_key_path is None:
            return None
        path = Path(self.jwt_private_key_path)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    @property
    def jwt_public_key(self) -> Optional[str]:
        if self.jwt_public_key_path is None:
            return None
        path = Path(self.jwt_public_key_path)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    @property
    def database_url_sync(self) -> str:
        return self.database_url.replace("+asyncpg", "").replace("+psycopg", "")

    @property
    def effective_jwt_algorithm(self) -> str:
        if self.jwt_algorithm.upper() in {"RS256", "ES256"}:
            if self.jwt_private_key is None or self.jwt_public_key is None:
                return self.jwt_algorithm_fallback
        return self.jwt_algorithm


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
