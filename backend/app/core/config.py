"""
Application Configuration
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

    # Application
    PROJECT_NAME: str = "Spond Admin API"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./spond_admin.db",
        description="Async database URL"
    )

    # Security
    SECRET_KEY: str = Field(
        ...,  # Required, no default
        description="Secret key for JWT tokens (minimum 32 characters)"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour (reduced from 7 days for security)

    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate that SECRET_KEY is properly configured"""
        if v == "change-me-in-production-use-openssl-rand-hex-32":
            raise ValueError(
                "SECRET_KEY must be changed from the default value! "
                "Generate a secure key with: openssl rand -hex 32"
            )
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long for security. "
                "Generate a secure key with: openssl rand -hex 32"
            )
        return v

    # Spond API Credentials
    SPOND_USERNAME: str = Field(
        default="",
        description="Spond account email"
    )
    SPOND_PASSWORD: str = Field(
        default="",
        description="Spond account password"
    )

    # Cache Settings
    CACHE_TTL_EVENTS: int = 300  # 5 minutes
    CACHE_TTL_GROUPS: int = 3600  # 1 hour
    CACHE_TTL_MEMBERS: int = 3600  # 1 hour

    # Sync Settings
    AUTO_SYNC_ENABLED: bool = True
    SYNC_INTERVAL_MINUTES: int = 15


# Create global settings instance
settings = Settings()
