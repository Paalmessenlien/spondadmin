"""
Scraper management API endpoints
"""
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.session import get_db, AsyncSessionLocal
from app.models.admin import Admin
from app.models.bueskyting_scrape_log import BueskytingScrapeLog
from app.services.bueskyting_scraper_service import BueskytingScraperService
from app.services.archer_matching_service import ArcherMatchingService
from app.services.scraping_config_service import ScrapingConfigService
from app.schemas.scrape import (
    ScrapeLogResponse,
    ScrapeLogListResponse,
    ScrapingConfigResponse,
    ScrapingConfigUpdate,
    UnmatchedArcherResponse,
    ArcherMatchRequest,
    ScrapeRunRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def _is_scrape_running(db: AsyncSession) -> bool:
    """Check if a scrape is currently running by querying the DB."""
    result = await db.execute(
        select(func.count(BueskytingScrapeLog.id)).where(
            BueskytingScrapeLog.status == "running"
        )
    )
    return (result.scalar() or 0) > 0


async def _run_scrape_background(scrape_type: str, **kwargs):
    """Run a scrape in the background with its own DB session."""
    try:
        async with AsyncSessionLocal() as db:
            config = await ScrapingConfigService.get_config(db)

            if scrape_type == "full":
                await BueskytingScraperService.scrape_full(
                    db, config, mode=kwargs.get("mode", "incremental")
                )
            elif scrape_type == "records":
                await BueskytingScraperService.scrape_records(db, config)
            elif scrape_type == "single_archer":
                archer_id = kwargs.get("archer_id")
                if not archer_id:
                    raise ValueError("archer_id required for single_archer scrape")
                await BueskytingScraperService.scrape_archer(
                    db, archer_id, config, mode=kwargs.get("mode", "incremental")
                )
            elif scrape_type == "event_dates":
                await BueskytingScraperService.scrape_event_dates(db, config)

            await db.commit()
    except Exception as e:
        logger.error(f"Background scrape failed: {e}", exc_info=True)
        # Mark any stuck "running" logs as failed
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(BueskytingScrapeLog).where(
                        BueskytingScrapeLog.status == "running"
                    )
                )
                for log in result.scalars().all():
                    log.status = "failed"
                    log.error_message = str(e)
                await db.commit()
        except Exception:
            logger.error("Failed to mark running logs as failed", exc_info=True)


@router.post("/run")
async def trigger_scrape(
    request: ScrapeRunRequest,
    background_tasks: BackgroundTasks,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a scraping operation."""
    if await _is_scrape_running(db):
        raise HTTPException(status_code=409, detail="A scrape is already running")

    # Validate config
    config = await ScrapingConfigService.get_config(db)
    if not config.club_id and request.type in ("full", "single_archer"):
        raise HTTPException(
            status_code=400,
            detail="Club ID not configured. Set it via PUT /scraper/config first.",
        )

    background_tasks.add_task(
        _run_scrape_background,
        request.type,
        archer_id=request.archer_id,
        mode=request.mode,
    )

    return {"status": "started", "type": request.type}


@router.get("/status")
async def get_scrape_status(
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get current scrape status."""
    return {"running": await _is_scrape_running(db)}


@router.get("/logs", response_model=ScrapeLogListResponse)
async def get_scrape_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get scrape history."""
    total = (
        await db.execute(select(func.count(BueskytingScrapeLog.id)))
    ).scalar() or 0

    result = await db.execute(
        select(BueskytingScrapeLog)
        .order_by(BueskytingScrapeLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    logs = result.scalars().all()

    return ScrapeLogListResponse(
        logs=[ScrapeLogResponse.model_validate(l) for l in logs],
        total=total,
    )


@router.get("/config", response_model=ScrapingConfigResponse)
async def get_scraping_config(
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get scraping configuration."""
    config = await ScrapingConfigService.get_config(db)
    await db.commit()
    return ScrapingConfigResponse.model_validate(config)


@router.put("/config", response_model=ScrapingConfigResponse)
async def update_scraping_config(
    data: ScrapingConfigUpdate,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update scraping configuration."""
    config = await ScrapingConfigService.update_config(db, data)
    await db.commit()
    return ScrapingConfigResponse.model_validate(config)


@router.get("/unmatched")
async def list_unmatched_archers(
    include_dismissed: bool = Query(False),
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List unmatched archers."""
    archers = await ArcherMatchingService.get_unmatched(db, include_dismissed)
    return {
        "archers": [UnmatchedArcherResponse.model_validate(a) for a in archers],
        "total": len(archers),
    }


@router.post("/match")
async def match_archer(
    request: ArcherMatchRequest,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manually link a bueskyting.no archer to a Spond member."""
    try:
        result = await ArcherMatchingService.manual_match(
            db, request.bueskyting_id, request.spond_id
        )
        await db.commit()
        return result
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/dismiss/{unmatched_id}")
async def dismiss_unmatched(
    unmatched_id: int,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss an unmatched archer."""
    await ArcherMatchingService.dismiss_unmatched(db, unmatched_id)
    await db.commit()
    return {"status": "dismissed"}


@router.post("/auto-match")
async def run_auto_match(
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Run auto-matching for unmatched archers."""
    result = await ArcherMatchingService.auto_match_archers(db)
    await db.commit()
    return result
