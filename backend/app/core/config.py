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
    CLUB_NAME: str = "Archery Club"
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
    # SECRET_KEY is still required: app/core/encryption.py derives a Fernet
    # key from it to encrypt AI provider API keys in the database.
    # JWT issuance is gone (Clerk handles tokens now), so the legacy
    # ALGORITHM / ACCESS_TOKEN_EXPIRE_MINUTES knobs were removed.
    SECRET_KEY: str = Field(
        ...,
        description="Secret key used for Fernet-encrypted secrets (min 32 chars)"
    )

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

    # Clerk Auth
    CLERK_PUBLISHABLE_KEY: str = Field(
        default="",
        description="Clerk publishable key (pk_test_... or pk_live_...)"
    )
    CLERK_SECRET_KEY: str = Field(
        default="",
        description="Clerk secret key (sk_test_... or sk_live_...) - server-side only"
    )
    CLERK_ISSUER: str = Field(
        default="",
        description="Clerk issuer URL, e.g. https://your-instance.clerk.accounts.dev"
    )
    CLERK_AUTHORIZED_PARTIES: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed origins for the azp claim in Clerk tokens"
    )
    CLERK_API_BASE: str = Field(
        default="https://api.clerk.com/v1",
        description="Clerk backend API base URL"
    )

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

    # Sync Settings (Legacy - kept for backwards compatibility)
    AUTO_SYNC_ENABLED: bool = True
    SYNC_INTERVAL_MINUTES: int = 15

    # Background Scheduler Settings
    # Events sync
    SYNC_EVENTS_ENABLED: bool = Field(
        default=True,
        description="Enable automatic events synchronization"
    )
    SYNC_EVENTS_INTERVAL_MINUTES: int = Field(
        default=60,
        description="Interval in minutes for events sync (default 1 hour)"
    )
    SYNC_EVENTS_MAX_EVENTS: int = Field(
        default=500,
        description="Maximum events to sync per run"
    )

    # Groups sync
    SYNC_GROUPS_ENABLED: bool = Field(
        default=True,
        description="Enable automatic groups synchronization"
    )
    SYNC_GROUPS_INTERVAL_MINUTES: int = Field(
        default=360,
        description="Interval in minutes for groups sync (default 6 hours)"
    )

    # Members sync
    SYNC_MEMBERS_ENABLED: bool = Field(
        default=True,
        description="Enable automatic members synchronization"
    )
    SYNC_MEMBERS_INTERVAL_MINUTES: int = Field(
        default=360,
        description="Interval in minutes for members sync (default 6 hours)"
    )

    # Bueskyting.no scraper settings
    BUESKYTING_BASE_URL: str = Field(
        default="https://resultat.bueskyting.no",
        description="Base URL for bueskyting.no results"
    )
    BUESKYTING_RECORDS_URL: str = Field(
        default="https://rekord.bueskyting.no",
        description="Base URL for bueskyting.no records"
    )
    BUESKYTING_CLUB_ID: str = Field(
        default="",
        description="Club ID on bueskyting.no"
    )

    # Bunny CDN (Backup Storage)
    BUNNY_STORAGE_ZONE: str = Field(
        default="",
        description="Bunny CDN storage zone name"
    )
    BUNNY_STORAGE_API_KEY: str = Field(
        default="",
        description="Bunny CDN storage API key"
    )
    BUNNY_CDN_HOSTNAME: str = Field(
        default="",
        description="Bunny CDN hostname for public URLs"
    )
    BUNNY_STORAGE_REGION: str = Field(
        default="",
        description="Bunny CDN storage region (empty for default)"
    )

    # Production
    GUNICORN_WORKERS: int = Field(
        default=4,
        description="Number of uvicorn workers in production"
    )


# Create global settings instance
settings = Settings()
