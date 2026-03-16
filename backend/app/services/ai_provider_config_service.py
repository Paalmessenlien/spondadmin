"""
AI Provider Config service - manages provider configurations with encrypted API keys
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_provider_config import AIProviderConfig
from app.core.encryption import encrypt_value, decrypt_value
from app.schemas.ai_provider import AIProviderUpdate


PROVIDERS = {
    "openai": {
        "display_name": "OpenAI",
        "default_model": "gpt-4o",
    },
    "anthropic": {
        "display_name": "Anthropic (Claude)",
        "default_model": "claude-sonnet-4-20250514",
    },
    "deepseek": {
        "display_name": "DeepSeek",
        "default_model": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
    },
}


class AIProviderConfigService:
    @staticmethod
    async def _ensure_providers(db: AsyncSession) -> None:
        """Create default rows for any missing providers."""
        result = await db.execute(select(AIProviderConfig))
        existing = {c.provider for c in result.scalars().all()}

        now = datetime.utcnow()
        for provider_key, defaults in PROVIDERS.items():
            if provider_key not in existing:
                config = AIProviderConfig(
                    provider=provider_key,
                    display_name=defaults["display_name"],
                    default_model=defaults["default_model"],
                    base_url=defaults.get("base_url"),
                    is_enabled=False,
                    created_at=now,
                    updated_at=now,
                )
                db.add(config)
        await db.flush()

    @staticmethod
    async def get_all(db: AsyncSession) -> List[AIProviderConfig]:
        """Get all provider configs, creating defaults for any missing."""
        await AIProviderConfigService._ensure_providers(db)
        result = await db.execute(
            select(AIProviderConfig).order_by(AIProviderConfig.provider)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_provider(db: AsyncSession, provider: str) -> Optional[AIProviderConfig]:
        """Get a single provider config, creating default if missing."""
        await AIProviderConfigService._ensure_providers(db)
        result = await db.execute(
            select(AIProviderConfig).where(AIProviderConfig.provider == provider)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_provider(
        db: AsyncSession, provider: str, data: AIProviderUpdate
    ) -> AIProviderConfig:
        """Update a provider config, encrypting the API key if provided."""
        config = await AIProviderConfigService.get_by_provider(db, provider)
        if not config:
            raise ValueError(f"Unknown provider: {provider}")

        update_data = data.model_dump(exclude_unset=True)

        # Handle API key encryption
        if "api_key" in update_data:
            api_key = update_data.pop("api_key")
            if api_key:
                config.api_key_encrypted = encrypt_value(api_key)
            else:
                config.api_key_encrypted = None

        for key, value in update_data.items():
            setattr(config, key, value)

        config.updated_at = datetime.utcnow()
        await db.flush()
        return config

    @staticmethod
    async def get_first_enabled(db: AsyncSession) -> Optional[AIProviderConfig]:
        """Get the first enabled provider with an API key configured."""
        await AIProviderConfigService._ensure_providers(db)
        result = await db.execute(
            select(AIProviderConfig)
            .where(
                AIProviderConfig.is_enabled == True,
                AIProviderConfig.api_key_encrypted.isnot(None),
            )
            .order_by(AIProviderConfig.provider)
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def get_decrypted_key(config: AIProviderConfig) -> Optional[str]:
        """Decrypt the API key from a provider config."""
        if not config.api_key_encrypted:
            return None
        return decrypt_value(config.api_key_encrypted)
