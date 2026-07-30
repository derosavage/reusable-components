from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Settings:
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    PROJECT_NAME: str = "Reusable Backend Platform"
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/backend")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_MAX_CONNECTIONS: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
    JWT_SECRET: str = os.getenv("JWT_SECRET", "jwt-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRY: int = int(os.getenv("JWT_ACCESS_EXPIRY", "900"))
    JWT_REFRESH_EXPIRY: int = int(os.getenv("JWT_REFRESH_EXPIRY", "604800"))
    ARGON2_TIME_COST: int = int(os.getenv("ARGON2_TIME_COST", "2"))
    ARGON2_MEMORY_COST: int = int(os.getenv("ARGON2_MEMORY_COST", "19456"))
    ARGON2_PARALLELISM: int = int(os.getenv("ARGON2_PARALLELISM", "1"))
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    DARAJA_CONSUMER_KEY: str = os.getenv("DARAJA_CONSUMER_KEY", "")
    DARAJA_CONSUMER_SECRET: str = os.getenv("DARAJA_CONSUMER_SECRET", "")
    DARAJA_PASSKEY: str = os.getenv("DARAJA_PASSKEY", "")
    DARAJA_SHORTCODE: str = os.getenv("DARAJA_SHORTCODE", "174379")
    DARAJA_ENV: str = os.getenv("DARAJA_ENV", "sandbox")
    DARAJA_CALLBACK_URL: str = os.getenv("DARAJA_CALLBACK_URL", "https://example.com/api/v1/daraja/callback")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_DEFAULT_MODEL: str = os.getenv("LLM_DEFAULT_MODEL", "openai/gpt-4o")
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    ANALYTICS_UPLOAD_DIR: str = os.getenv("ANALYTICS_UPLOAD_DIR", "/tmp/uploads")
    ANALYTICS_MAX_FILE_SIZE: int = int(os.getenv("ANALYTICS_MAX_FILE_SIZE", "104857600"))
    DUCKDB_PATH: str = os.getenv("DUCKDB_PATH", ":memory:")
    STORAGE_ENDPOINT: str = os.getenv("STORAGE_ENDPOINT", "localhost:9000")
    STORAGE_ACCESS_KEY: str = os.getenv("STORAGE_ACCESS_KEY", "minioadmin")
    STORAGE_SECRET_KEY: str = os.getenv("STORAGE_SECRET_KEY", "minioadmin")
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "backend-storage")
    STORAGE_REGION: str = os.getenv("STORAGE_REGION", "us-east-1")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
    ANALYTICS_SERVICE_URL: str = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8002")
    DATA_FACTORY_URL: str = os.getenv("DATA_FACTORY_URL", "http://data-factory:8003")
    DARAJA_SERVICE_URL: str = os.getenv("DARAJA_SERVICE_URL", "http://daraja-service:8004")
    LLM_SERVICE_URL: str = os.getenv("LLM_SERVICE_URL", "http://llm-service:8005")
    CORS_ORIGINS: List[str] = field(default_factory=lambda: ["*"])

    PERMISSION_BITS: Dict[str, int] = field(default_factory=lambda: {
        "users:read": 1 << 0,
        "users:write": 1 << 1,
        "users:delete": 1 << 2,
        "roles:manage": 1 << 3,
        "analytics:read": 1 << 4,
        "analytics:write": 1 << 5,
        "analytics:delete": 1 << 6,
        "data:read": 1 << 7,
        "data:write": 1 << 8,
        "llm:query": 1 << 9,
        "admin": 1 << 10,
        "daraja:initiate": 1 << 11,
        "daraja:read": 1 << 12,
    })

    ROLE_BITS: Dict[str, int] = field(default_factory=lambda: {
        "admin": (1 << 11) - 1,
        "analyst": (1 << 4) | (1 << 5) | (1 << 7) | (1 << 8) | (1 << 9),
        "trader": (1 << 7) | (1 << 8) | (1 << 9) | (1 << 11) | (1 << 12),
        "viewer": (1 << 4) | (1 << 7) | (1 << 9),
    })

    def has_permission(self, role_bitmask: int, permission_name: str) -> bool:
        perm_bit = self.PERMISSION_BITS.get(permission_name, 0)
        return (role_bitmask & perm_bit) == perm_bit

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"


settings = Settings()
