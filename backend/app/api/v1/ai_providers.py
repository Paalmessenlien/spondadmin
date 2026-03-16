"""
AI Provider configuration API endpoints
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.admin import Admin
from app.services.ai_provider_config_service import AIProviderConfigService
from app.services.ai_service import AIService
from app.schemas.ai_provider import (
    AIProviderResponse,
    AIProviderUpdate,
    AIProviderTestResponse,
    AIModelsResponse,
    AIModelOption,
)

logger = logging.getLogger(__name__)
router = APIRouter()

PROVIDER_MODELS = {
    "openai": [
        AIModelOption(id="gpt-4o", name="GPT-4o"),
        AIModelOption(id="gpt-4o-mini", name="GPT-4o Mini"),
        AIModelOption(id="gpt-4-turbo", name="GPT-4 Turbo"),
        AIModelOption(id="o1", name="o1"),
        AIModelOption(id="o3-mini", name="o3 Mini"),
    ],
    "anthropic": [
        AIModelOption(id="claude-sonnet-4-20250514", name="Claude Sonnet 4"),
        AIModelOption(id="claude-opus-4-20250514", name="Claude Opus 4"),
        AIModelOption(id="claude-haiku-4-20250514", name="Claude Haiku 4"),
    ],
    "deepseek": [
        AIModelOption(id="deepseek-chat", name="DeepSeek Chat"),
        AIModelOption(id="deepseek-reasoner", name="DeepSeek Reasoner"),
    ],
}


def _config_to_response(config) -> AIProviderResponse:
    """Convert a config model to response schema."""
    return AIProviderResponse(
        id=config.id,
        provider=config.provider,
        display_name=config.display_name,
        has_api_key=bool(config.api_key_encrypted),
        base_url=config.base_url,
        default_model=config.default_model,
        is_enabled=config.is_enabled,
        last_tested_at=config.last_tested_at,
        test_status=config.test_status,
        test_error=config.test_error,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("/providers", response_model=List[AIProviderResponse])
async def list_providers(
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
):
    """List all AI provider configurations."""
    configs = await AIProviderConfigService.get_all(db)
    await db.commit()
    return [_config_to_response(c) for c in configs]


@router.get("/providers/{provider}", response_model=AIProviderResponse)
async def get_provider(
    provider: str,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
):
    """Get a single AI provider configuration."""
    config = await AIProviderConfigService.get_by_provider(db, provider)
    await db.commit()
    if not config:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")
    return _config_to_response(config)


@router.put("/providers/{provider}", response_model=AIProviderResponse)
async def update_provider(
    provider: str,
    data: AIProviderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
):
    """Update an AI provider configuration."""
    try:
        config = await AIProviderConfigService.update_provider(db, provider, data)
        await db.commit()
        return _config_to_response(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/providers/{provider}/test", response_model=AIProviderTestResponse)
async def test_provider(
    provider: str,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
):
    """Test AI provider credentials with a simple request."""
    result = await AIService.test_credentials(db, provider)
    await db.commit()
    return result


@router.get("/models/{provider}", response_model=AIModelsResponse)
async def get_provider_models(
    provider: str,
    current_user: Admin = Depends(get_current_admin),
):
    """Get available models for a provider."""
    models = PROVIDER_MODELS.get(provider)
    if models is None:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")
    return AIModelsResponse(provider=provider, models=models)
