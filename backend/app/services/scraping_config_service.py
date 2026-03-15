"""
Scraping Config service - singleton config management
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scraping_config import ScrapingConfig
from app.schemas.scrape import ScrapingConfigUpdate


class ScrapingConfigService:
    @staticmethod
    async def get_config(db: AsyncSession) -> ScrapingConfig:
        """Get the scraping config singleton, creating it if it doesn't exist."""
        result = await db.execute(select(ScrapingConfig).limit(1))
        config = result.scalar_one_or_none()
        if not config:
            now = datetime.now(timezone.utc)
            config = ScrapingConfig(
                created_at=now,
                updated_at=now,
            )
            db.add(config)
            await db.flush()
        return config

    @staticmethod
    async def update_config(
        db: AsyncSession, data: ScrapingConfigUpdate
    ) -> ScrapingConfig:
        """Update scraping configuration."""
        config = await ScrapingConfigService.get_config(db)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)
        config.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return config
