"""
Application Configuration with Fail-Fast Validation

Uses pydantic-settings to validate all required environment variables at
startup.  In production the app will crash immediately with a clear error
if critical secrets are missing, rather than discovering the gap at runtime.
"""

from __future__ import annotations

import os
from typing import List, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralised, validated application settings.

    All values are loaded from environment variables (or a .env file via
    ``env_file``).  Fields marked ``Optional`` have sensible defaults for
    local development; required fields will cause a startup crash if absent
    in production.
    """

    # ── Environment ─────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"

    # ── Database ────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./smarty_neural_core.db"

    # ── Auth / JWT ──────────────────────────────────────────────────────
    JWT_SECRET_KEY: Optional[str] = None
    SECRET_KEY: Optional[str] = None
    ADMIN_PASSWORD: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── AI / ML ─────────────────────────────────────────────────────────
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # ── FemmeCare Encryption ────────────────────────────────────────────
    FEMME_SECRET_KEY: Optional[str] = None

    # ── CORS ────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    # ── Redis (optional) ────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Clerk (optional overlay) ────────────────────────────────────────
    CLERK_SECRET_KEY: Optional[str] = None

    # ── Convenience helpers ─────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in {"production", "prod"}

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT.lower() in {"test", "testing"} or bool(
            os.getenv("PYTEST_CURRENT_TEST")
        )

    @property
    def effective_secret_key(self) -> str:
        """Return the secret key, falling back to a stable dev-only value."""
        key = self.JWT_SECRET_KEY or self.SECRET_KEY
        if key:
            return key
        if self.is_production:
            raise RuntimeError(
                "JWT_SECRET_KEY or SECRET_KEY must be set in production"
            )
        return "smarty-local-dev-secret-key"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ── Production guards ───────────────────────────────────────────────
    @model_validator(mode="after")
    def _enforce_production_requirements(self) -> "Settings":
        if not self.is_production:
            return self

        missing: list[str] = []

        if not (self.JWT_SECRET_KEY or self.SECRET_KEY):
            missing.append("JWT_SECRET_KEY or SECRET_KEY")

        if not self.FEMME_SECRET_KEY:
            missing.append("FEMME_SECRET_KEY")

        if self.DATABASE_URL.startswith("sqlite"):
            missing.append(
                "DATABASE_URL (must be a PostgreSQL connection string "
                "in production, not SQLite)"
            )

        cors = self.cors_origins_list
        if "*" in cors or len(cors) == 0:
            missing.append(
                "CORS_ORIGINS (wildcard or empty origins not allowed "
                "in production)"
            )

        if missing:
            bullet_list = "\n  • ".join(missing)
            raise ValueError(
                "Production environment is missing required configuration:"
                f"\n  • {bullet_list}\n"
                "Set these environment variables before starting the server."
            )

        return self

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def get_settings() -> Settings:
    """Singleton accessor – import and call once at module level."""
    return Settings()
