"""
Authentication API endpoints
"""
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_access_token
from app.core.deps import get_current_user, get_current_superuser
from app.db.session import get_db
from app.models.admin import Admin
from app.schemas.admin import (
    AdminCreate,
    AdminUpdate,
    AdminResponse,
    AdminLogin,
)
from app.schemas.token import Token, RefreshTokenRequest
from app.services.admin_service import AdminService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # Allow 5 login attempts per minute per IP
async def login(
    request: Request,
    login_data: AdminLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    Login endpoint - authenticate and return JWT token

    Rate limit: 5 attempts per minute per IP address

    Args:
        request: FastAPI request object (required for rate limiting)
        login_data: Login credentials (username and password)
        db: Database session

    Returns:
        JWT access token

    Raises:
        HTTPException: If credentials are invalid
    """
    admin = await AdminService.authenticate(
        db,
        username=login_data.username,
        password=login_data.password
    )

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token and refresh token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(admin.id)},
        expires_delta=access_token_expires
    )

    refresh_token = create_refresh_token(
        data={"sub": str(admin.id)}
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")  # Allow 10 refresh attempts per minute per IP
async def refresh_token(
    request: Request,
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using a refresh token

    Rate limit: 10 attempts per minute per IP address

    Args:
        request: FastAPI request object (required for rate limiting)
        refresh_request: Refresh token request containing the refresh token
        db: Database session

    Returns:
        New access token and refresh token

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    # Decode and verify refresh token
    payload = decode_access_token(refresh_request.refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists and is active
    admin = await AdminService.get_by_id(db, int(user_id))
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new access token and refresh token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(admin.id)},
        expires_delta=access_token_expires
    )

    new_refresh_token = create_refresh_token(
        data={"sub": str(admin.id)}
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=new_refresh_token
    )


@router.get("/me", response_model=AdminResponse)
async def get_current_user_info(
    current_user: Admin = Depends(get_current_user),
):
    """
    Get current user information

    Args:
        current_user: Current authenticated user

    Returns:
        Current user data
    """
    return current_user


@router.put("/me", response_model=AdminResponse)
async def update_current_user(
    update_data: AdminUpdate,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user information

    Args:
        update_data: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user data

    Raises:
        HTTPException: If update fails
    """
    # Don't allow users to change their own superuser status
    if update_data.is_superuser is not None:
        update_data.is_superuser = current_user.is_superuser

    try:
        updated_admin = await AdminService.update(db, current_user.id, update_data)
        if not updated_admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        await db.commit()
        return updated_admin
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/register", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")  # Allow 10 admin registrations per hour per IP
async def register_admin(
    request: Request,
    admin_data: AdminCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_superuser),
):
    """
    Register a new admin (superuser only)

    Rate limit: 10 registrations per hour per IP address

    Args:
        request: FastAPI request object (required for rate limiting)
        admin_data: Admin creation data
        db: Database session
        current_user: Current superuser

    Returns:
        Created admin data

    Raises:
        HTTPException: If creation fails
    """
    try:
        admin = await AdminService.create(db, admin_data)
        await db.commit()
        return admin
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/admins", response_model=List[AdminResponse])
async def list_admins(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_superuser),
):
    """
    List all admins (superuser only)

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current superuser

    Returns:
        List of admins
    """
    admins = await AdminService.get_all(db, skip=skip, limit=limit)
    return admins


@router.get("/admins/{admin_id}", response_model=AdminResponse)
async def get_admin(
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_superuser),
):
    """
    Get a specific admin by ID (superuser only)

    Args:
        admin_id: Admin ID
        db: Database session
        current_user: Current superuser

    Returns:
        Admin data

    Raises:
        HTTPException: If admin not found
    """
    admin = await AdminService.get_by_id(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    return admin


@router.put("/admins/{admin_id}", response_model=AdminResponse)
async def update_admin(
    admin_id: int,
    update_data: AdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_superuser),
):
    """
    Update an admin (superuser only)

    Args:
        admin_id: Admin ID
        update_data: Update data
        db: Database session
        current_user: Current superuser

    Returns:
        Updated admin data

    Raises:
        HTTPException: If update fails
    """
    try:
        admin = await AdminService.update(db, admin_id, update_data)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        await db.commit()
        return admin
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/admins/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_superuser),
):
    """
    Delete an admin (superuser only)

    Args:
        admin_id: Admin ID
        db: Database session
        current_user: Current superuser

    Raises:
        HTTPException: If admin not found or cannot delete self
    """
    # Prevent deleting self
    if admin_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    success = await AdminService.delete(db, admin_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    await db.commit()
