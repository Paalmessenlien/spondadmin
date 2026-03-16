"""
Pydantic schemas for AI provider configuration
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class AIProviderResponse(BaseModel):
    id: int
    provider: str
    display_name: str
    has_api_key: bool
    base_url: Optional[str] = None
    default_model: str
    is_enabled: bool
    last_tested_at: Optional[datetime] = None
    test_status: Optional[str] = None
    test_error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AIProviderUpdate(BaseModel):
    api_key: Optional[str] = Field(None, description="Plaintext API key (will be encrypted)")
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    is_enabled: Optional[bool] = None


class AIProviderTestResponse(BaseModel):
    provider: str
    status: str
    message: str
    model_used: Optional[str] = None
    response_time_ms: Optional[int] = None


class AIChatRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    messages: List[Dict[str, str]]
    max_tokens: int = 1024
    temperature: float = 0.7


class AIChatResponse(BaseModel):
    provider: str
    model: str
    content: str
    usage: Optional[Dict] = None


class AIModelOption(BaseModel):
    id: str
    name: str


class AIModelsResponse(BaseModel):
    provider: str
    models: List[AIModelOption]
