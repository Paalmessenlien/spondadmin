"""
Archery Club Administration - FastAPI Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.db.session import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown events
    """
    # Startup
    logger.info("Starting up Archery Club Admin API...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Start background scheduler
    if settings.AUTO_SYNC_ENABLED:
        from app.services.scheduler_service import scheduler_service
        try:
            await scheduler_service.start()
            logger.info("Background scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start background scheduler: {e}")
            # Don't raise - allow app to start even if scheduler fails

    yield

    # Shutdown
    logger.info("Shutting down Archery Club Admin API...")

    # Stop background scheduler
    if settings.AUTO_SYNC_ENABLED:
        from app.services.scheduler_service import scheduler_service
        try:
            await scheduler_service.stop()
            logger.info("Background scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping background scheduler: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Archery club administration with Spond integration",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with consistent format
    """
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    errors = []
    for err in exc.errors():
        err = dict(err)
        if isinstance(err.get("input"), bytes):
            err["input"] = err["input"].decode("utf-8", errors="replace")
        errors.append(err)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": errors,
            "body": exc.body.decode("utf-8", errors="replace") if isinstance(getattr(exc, 'body', None), bytes) else (exc.body if hasattr(exc, 'body') else None),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected errors with consistent format
    """
    logger.exception(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint - validates DB connectivity"""
    from sqlalchemy import text
    from app.db.session import AsyncSessionLocal

    db_ok = False
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
            db_ok = True
    except Exception as e:
        logger.warning(f"Health check DB test failed: {e}")

    status = "healthy" if db_ok else "degraded"
    return {
        "status": status,
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "database": "connected" if db_ok else "unavailable",
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"{settings.CLUB_NAME} Admin API",
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }


# Include API routers
from fastapi import Depends
from app.api.v1 import auth, events, groups, members, analytics, scheduler, categories, reports, config_public, scores, scraper, backups, migrations, ai_providers, external_events, training, expenses, forms, projects, access
from app.core.modules import require_module


def _module_guard(module_key: str):
    """Router-level dependency gating every endpoint by module access."""
    return [Depends(require_module(module_key))]


# Ungated: auth (self + superuser-gated admin mgmt), groups (group selector
# used everywhere), config (public), categories (shared reference data).
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["auth"])
app.include_router(access.router, prefix=f"{settings.API_V1_PREFIX}/access", tags=["access"])
app.include_router(groups.router, prefix=f"{settings.API_V1_PREFIX}/groups", tags=["groups"])
app.include_router(config_public.router, prefix=f"{settings.API_V1_PREFIX}/config", tags=["config"])
app.include_router(categories.router, prefix=f"{settings.API_V1_PREFIX}/categories", tags=["categories"])

# Module-gated: each router maps to one sidebar module (see app/core/modules.py).
app.include_router(events.router, prefix=f"{settings.API_V1_PREFIX}/events", tags=["events"], dependencies=_module_guard("events"))
app.include_router(members.router, prefix=f"{settings.API_V1_PREFIX}/members", tags=["members"], dependencies=_module_guard("members"))
app.include_router(analytics.router, prefix=f"{settings.API_V1_PREFIX}/analytics", tags=["analytics"], dependencies=_module_guard("analytics"))
app.include_router(reports.router, prefix=f"{settings.API_V1_PREFIX}/reports", tags=["reports"], dependencies=_module_guard("reports"))
app.include_router(scores.router, prefix=f"{settings.API_V1_PREFIX}/scores", tags=["scores"], dependencies=_module_guard("scores"))
app.include_router(external_events.router, prefix=f"{settings.API_V1_PREFIX}/external-events", tags=["external-events"], dependencies=_module_guard("competitions"))
app.include_router(training.router, prefix=f"{settings.API_V1_PREFIX}/training", tags=["training"], dependencies=_module_guard("training"))
app.include_router(expenses.router, prefix=f"{settings.API_V1_PREFIX}/expenses", tags=["expenses"], dependencies=_module_guard("expenses"))
app.include_router(forms.router, prefix=f"{settings.API_V1_PREFIX}/forms", tags=["forms"], dependencies=_module_guard("forms"))
app.include_router(projects.router, prefix=f"{settings.API_V1_PREFIX}/projects", tags=["projects"], dependencies=_module_guard("projects"))

# Settings sub-features all gate on the "settings" module.
app.include_router(scheduler.router, prefix=f"{settings.API_V1_PREFIX}/scheduler", tags=["scheduler"], dependencies=_module_guard("settings"))
app.include_router(scraper.router, prefix=f"{settings.API_V1_PREFIX}/scraper", tags=["scraper"], dependencies=_module_guard("settings"))
app.include_router(backups.router, prefix=f"{settings.API_V1_PREFIX}/backups", tags=["backups"], dependencies=_module_guard("settings"))
app.include_router(migrations.router, prefix=f"{settings.API_V1_PREFIX}/migrations", tags=["migrations"], dependencies=_module_guard("settings"))
app.include_router(ai_providers.router, prefix=f"{settings.API_V1_PREFIX}/ai", tags=["ai"], dependencies=_module_guard("settings"))
