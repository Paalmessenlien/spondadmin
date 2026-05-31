"""
External Events API router - upcoming competitions from bueskyting.no
"""
import asyncio
import json
import logging
from datetime import date as DateType
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_current_admin
from app.db.session import get_db, AsyncSessionLocal
from app.models.admin import Admin
from app.models.competition import Competition
from app.models.event import Event
from app.schemas.external_event import (
    ExternalEventResponse,
    ExternalEventListResponse,
    ExternalEventFilters,
    ExternalEventLinkSuggestions,
    ExternalEventLinkRequest,
)
from app.services.competition_link_service import CompetitionLinkService
from app.services.external_event_service import ExternalEventService
from app.services.external_event_scraper_service import ExternalEventScraperService

logger = logging.getLogger(__name__)

router = APIRouter()

# Track active analyze-all tasks so they can be cancelled
_active_analysis_tasks: dict[str, bool] = {}


async def _attach_link_labels(db: AsyncSession, events: list) -> None:
    """Resolve linked_event_id → event heading and linked_competition_id →
    competition name, attaching them as transient attributes for display.
    Two batch queries. The numeric ids are used for navigation.
    """
    event_ids = {e.linked_event_id for e in events if e.linked_event_id}
    comp_ids = {e.linked_competition_id for e in events if e.linked_competition_id}
    headings: dict[int, str] = {}
    names: dict[int, str] = {}
    if event_ids:
        rows = await db.execute(
            select(Event.id, Event.heading).where(Event.id.in_(event_ids))
        )
        headings = {eid: h for eid, h in rows.all()}
    if comp_ids:
        rows = await db.execute(
            select(Competition.id, Competition.name).where(Competition.id.in_(comp_ids))
        )
        names = {cid: n for cid, n in rows.all()}
    for e in events:
        e.linked_event_heading = headings.get(e.linked_event_id)
        e.linked_competition_name = names.get(e.linked_competition_id)


@router.get("/", response_model=ExternalEventListResponse)
async def list_external_events(
    search: Optional[str] = Query(None),
    date_from: Optional[DateType] = Query(None),
    date_to: Optional[DateType] = Query(None),
    ai_event_category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List external events with filtering and pagination."""
    filters = ExternalEventFilters(
        search=search,
        date_from=date_from,
        date_to=date_to,
        ai_event_category=ai_event_category,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    events, total = await ExternalEventService.get_events(db, filters)
    await _attach_link_labels(db, list(events))
    return ExternalEventListResponse(
        events=[ExternalEventResponse.model_validate(e) for e in events],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{event_id}", response_model=ExternalEventResponse)
async def get_external_event(
    event_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single external event by ID."""
    event = await ExternalEventService.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await _attach_link_labels(db, [event])
    return ExternalEventResponse.model_validate(event)


@router.get(
    "/{event_id}/link-suggestions",
    response_model=ExternalEventLinkSuggestions,
)
async def get_link_suggestions(
    event_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Suggest local Spond events / competitions that match this external
    competition (date proximity + fuzzy name). Suggestions only — confirm via
    POST /{id}/link."""
    event = await ExternalEventService.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    suggestions = await CompetitionLinkService.suggest_links(db, event)
    return ExternalEventLinkSuggestions(**suggestions)


@router.post("/{event_id}/link", response_model=ExternalEventResponse)
async def set_external_event_link(
    event_id: int,
    payload: ExternalEventLinkRequest,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Confirm (or clear) the link from this external competition to a local
    Spond event and/or competition. Only the fields present in the request body
    are changed; pass an explicit null to clear one side."""
    event = await ExternalEventService.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Merge: only overwrite a side that was explicitly provided (present in the
    # JSON body), so a partial request doesn't clobber the other link.
    sent = payload.model_fields_set
    new_event_id = payload.event_id if "event_id" in sent else event.linked_event_id
    new_comp_id = (
        payload.competition_id
        if "competition_id" in sent
        else event.linked_competition_id
    )
    try:
        await CompetitionLinkService.set_link(
            db, event, event_id=new_event_id, competition_id=new_comp_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await db.commit()
    # Re-fetch fresh so the response isn't built from attributes the flush
    # expired (server-side updated_at) — avoids a sync lazy-load on an async
    # session. Mirrors the training shift reload pattern.
    event = await ExternalEventService.get_event_by_id(db, event_id)
    await _attach_link_labels(db, [event])
    return ExternalEventResponse.model_validate(event)


@router.post("/scrape")
async def scrape_external_events(
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Trigger scraping of upcoming events from bueskyting.no terminliste."""
    try:
        stats = await ExternalEventScraperService.scrape_upcoming_events(db)
        await db.commit()
        return {"status": "success", "message": "Scraping complete", "stats": stats}
    except Exception as e:
        logger.error(f"Scrape failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@router.post("/{event_id}/analyze")
async def analyze_external_event(
    event_id: int,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Re-run AI analysis on a single external event."""
    event = await ExternalEventService.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    try:
        result = await ExternalEventScraperService.analyze_event_with_ai(db, event)
        await db.commit()
        if "error" in result and "category" not in result:
            # Config-level error (no provider enabled, no API key, etc.)
            raise HTTPException(status_code=400, detail=result["error"])
        # If category is present, analysis succeeded (even if partially)
        return {"status": "success", **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI analysis failed for event {event_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze-all")
async def analyze_all_external_events(
    request: Request,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Run AI analysis on all un-analyzed external events.
    Returns a Server-Sent Events stream with progress updates.
    """
    events = await ExternalEventService.get_unanalyzed_events(db)
    total_count = len(events)

    if total_count == 0:
        return {"status": "success", "message": "Ingen konkurranser å analysere", "analyzed": 0, "total": 0}

    # Check if AI is configured before starting the stream
    from app.services.ai_provider_config_service import AIProviderConfigService
    config = await AIProviderConfigService.get_first_enabled(db)
    if not config:
        raise HTTPException(
            status_code=400,
            detail="Ingen AI-leverandør er aktivert. Konfigurer en under Innstillinger > AI-leverandører."
        )

    # Collect event IDs to process (events are bound to current session)
    event_ids = [e.id for e in events]

    # Create a task ID for cancellation
    import uuid
    task_id = str(uuid.uuid4())
    _active_analysis_tasks[task_id] = True  # True = running

    async def event_stream():
        analyzed = 0
        errors = 0
        try:
            # Send initial event with task_id and total
            yield f"data: {json.dumps({'type': 'start', 'task_id': task_id, 'total': total_count})}\n\n"

            for i, event_id in enumerate(event_ids):
                # Check if cancelled
                if not _active_analysis_tasks.get(task_id, False):
                    yield f"data: {json.dumps({'type': 'cancelled', 'analyzed': analyzed, 'errors': errors, 'total': total_count})}\n\n"
                    return

                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"Client disconnected during analysis, stopping at {i}/{total_count}")
                    return

                # Use a fresh session for each event to avoid stale state
                async with AsyncSessionLocal() as session:
                    event = await ExternalEventService.get_event_by_id(session, event_id)
                    if not event:
                        errors += 1
                        continue

                    try:
                        result = await ExternalEventScraperService.analyze_event_with_ai(session, event)
                        await session.commit()
                        if "error" in result:
                            errors += 1
                        else:
                            analyzed += 1
                    except Exception as e:
                        logger.error(f"AI analysis failed for event {event_id}: {e}")
                        errors += 1

                # Send progress event
                yield f"data: {json.dumps({'type': 'progress', 'current': i + 1, 'total': total_count, 'analyzed': analyzed, 'errors': errors, 'event_name': event.name if event else '?'})}\n\n"

            # Send completion event
            yield f"data: {json.dumps({'type': 'done', 'analyzed': analyzed, 'errors': errors, 'total': total_count})}\n\n"

        finally:
            _active_analysis_tasks.pop(task_id, None)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/analyze-stop/{task_id}")
async def stop_analysis(
    task_id: str,
    current_user: Admin = Depends(get_current_admin),
):
    """Stop an in-progress analyze-all task."""
    if task_id in _active_analysis_tasks:
        _active_analysis_tasks[task_id] = False  # Signal cancellation
        return {"status": "success", "message": "Analyse stoppes..."}
    return {"status": "not_found", "message": "Oppgaven ble ikke funnet eller er allerede fullført"}
