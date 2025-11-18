"""
Database session management
"""
from typing import AsyncGenerator
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from app.core.config import settings
from app.db.base import Base

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """
    Initialize database - create all tables
    """
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with Base
        from app.models import admin, event, group, member, sync_history, audit_log  # noqa: F401

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions

    Note: This dependency does NOT auto-commit. Endpoints must explicitly
    call await db.commit() after successful operations to maintain proper
    transaction boundaries.

    Usage in FastAPI endpoints:
        async def endpoint(db: AsyncSession = Depends(get_db)):
            # Perform database operations
            ...
            # Explicitly commit when done
            await db.commit()
            return result
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Note: No auto-commit - endpoints control their own transactions
        except HTTPException:
            # Re-raise HTTP exceptions without rollback (they may be intentional)
            await session.rollback()
            raise
        except Exception:
            # Rollback on unexpected errors
            await session.rollback()
            raise
        finally:
            await session.close()
