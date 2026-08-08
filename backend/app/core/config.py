from __future__ import annotations

from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ─── App ──────────────────────────────────────────────
    app_name: str = "Performance-Safe Rightsizing Simulator"
    environment: str = "development"
    debug: bool = True

    # ─── Database ─────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://rss_user:rss_password@localhost:5432/rightsizing_db"

    # ─── JWT ──────────────────────────────────────────────
    secret_key: str = "change-me-to-a-long-random-string-at-least-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ─── Admin seed ────────────────────────────────────────
    admin_username: str = "admin"
    admin_password: str = "admin123"
    admin_email: str = "admin@example.com"

    # ─── Upload ───────────────────────────────────────────
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    # ─── CORS ─────────────────────────────────────────────
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str) -> str:
        return v

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


settings = Settings()
