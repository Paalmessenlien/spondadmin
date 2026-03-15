"""
Database session management
"""
from typing import AsyncGenerator
from fastapi import HTTPException
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from app.core.config import settings
from app.db.base import Base

# Build engine kwargs based on database type
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

_engine_kwargs = dict(
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL / other databases: configure connection pool
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 10

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

# Enable WAL mode and busy timeout for SQLite on every connection
if _is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

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
        from app.models import (  # noqa: F401
            admin, event, group, member, archer_profile, sync_history, audit_log,
            competition, competition_result, archer_statistics, archery_record,
            bueskyting_scrape_log, unmatched_archer, scraping_config,
            database_backup,
        )

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
