"""
Security utilities for authentication and password hashing
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing context with explicit bcrypt rounds
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Explicitly set rounds for security
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with proper timezone handling

    Args:
        data: Dictionary with payload data (e.g., {"sub": "user_id"})
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add standard JWT claims
    to_encode.update({
        "exp": expire,      # Expiration time
        "iat": now,         # Issued at
        "nbf": now,         # Not before
        "type": "access",   # Token type
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token with longer expiration

    Args:
        data: Dictionary with payload data (e.g., {"sub": "user_id"})
        expires_delta: Optional expiration time delta (default: 7 days)

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=7)  # Refresh tokens last 7 days

    # Add standard JWT claims
    to_encode.update({
        "exp": expire,      # Expiration time
        "iat": now,         # Issued at
        "nbf": now,         # Not before
        "type": "refresh",  # Token type
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT access token with explicit verification

    Args:
        token: JWT token string

    Returns:
        Decoded payload dictionary or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={
                "verify_exp": True,  # Explicitly verify expiration
                "verify_iat": True,  # Verify issued at
                "verify_nbf": True,  # Verify not before
            }
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None
