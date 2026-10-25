"""Application configuration module using Pydantic Settings.

Reads settings from environment variables or .env file.
"""

from pathlib import Path
from typing import List, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Canonical project root directory (API_Checker)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """Central application settings class."""

    # Project Information
    PROJECT_NAME: str = "RequestLab"
    PROJECT_DESCRIPTION: str = "A simplified, secure Postman-like API testing workspace."
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        """Parse debug flag safely, handling external OS variables like DEBUG='release'."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in ("true", "1", "t", "yes", "y", "enabled")
        return bool(v)

    # Security & JWT
    SECRET_KEY: str = "change-me-to-a-secure-random-secret-key-32-chars-min"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database connection string
    # Defaults to SQLite in the local directory
    DATABASE_URL: str = "sqlite:///./api_sentinel.db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def resolve_sqlite_path(cls, v: Any) -> str:
        """Resolve relative SQLite database paths to an absolute path at the project root.

        This guarantees that no matter what directory the server or migration is started from,
        the application always connects to the same migrated database file.
        """
        if isinstance(v, str) and v.startswith("sqlite:///."):
            rel_file = v.replace("sqlite:///.", "").lstrip("/\\")
            abs_db_path = (PROJECT_ROOT / rel_file).as_posix()
            return f"sqlite:///{abs_db_path}"
        return str(v)

    # CORS origins allowed to access the API (e.g. Vue frontend)
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # HTTP Outbound Request Limits (SSRF & DoS mitigation)
    OUTBOUND_REQUEST_TIMEOUT_SECONDS: float = 10.0
    OUTBOUND_MAX_RESPONSE_BYTES: int = 5 * 1024 * 1024  # 5 Megabytes
    OUTBOUND_MAX_REDIRECTS: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Singleton instance of settings to import across the application
settings = Settings()

