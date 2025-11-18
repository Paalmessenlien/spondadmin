"""
Token schemas for authentication
"""
from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """
    Access token response with optional refresh token
    """
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    """
    JWT token payload
    """
    sub: str  # Subject (user ID)
    exp: int  # Expiration timestamp
    type: str = "access"  # Token type: "access" or "refresh"


class RefreshTokenRequest(BaseModel):
    """
    Refresh token request
    """
    refresh_token: str
