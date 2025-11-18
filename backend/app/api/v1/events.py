"""
Events API endpoints
"""
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.admin import Admin
from app.schemas.event import (
    EventResponse,
    EventListResponse,
    EventCreate,
    EventUpdate,
    EventFilters,
    EventStats,
    EventResponseUpdate,
    EventSyncResult,
)
from app.services.event_service import EventService
from app.services.event_sync_service import EventSyncService
from app.services.spond_service import get_spond_service, SpondService

router = APIRouter()


@router.post("/sync", response_model=EventSyncResult)
async def sync_events(
    group_id: Optional[str] = None,
    max_events: int = 500,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    spond_service: SpondService = Depends(get_spond_service),
):
    """
    Sync events from Spond API to database

    Args:
        group_id: Optional group ID to filter events
        max_events: Maximum number of events to fetch (default 500)
        db: Database session
        current_user: Current authenticated user
        spond_service: Spond service instance

    Returns:
        Sync result with statistics
    """
    try:
        stats = await EventSyncService.sync_events(
            db,
            spond_service,
            group_id=group_id,
            max_events=max_events
        )

        await db.commit()

        return EventSyncResult(
            total_fetched=stats["fetched"],
            created=stats["created"],
            updated=stats["updated"],
            errors=stats["errors"],
            sync_time=datetime.now(timezone.utc),
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync events: {str(e)}"
        )


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    create_data: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    spond_service: SpondService = Depends(get_spond_service),
):
    """
    Create a new event

    Args:
        create_data: Event creation data
        db: Database session
        current_user: Current authenticated user
        spond_service: Spond service instance

    Returns:
        Created event

    Raises:
        HTTPException: If creation fails
    """
    try:
        event = await EventService.create(
            db,
            create_data,
            spond_service=spond_service if create_data.sync_to_spond else None
        )

        await db.commit()
        return event

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}"
        )


@router.get("", response_model=EventListResponse)
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    event_type: Optional[str] = None,
    include_cancelled: bool = False,
    include_hidden: bool = False,
    include_archived: bool = False,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    order_by: str = Query("start_time", regex="^(start_time|created_time|heading)$"),
    order_desc: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
):
    """
    List events with filtering and pagination

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        event_type: Filter by event type (AVAILABILITY, EVENT, RECURRING)
        include_cancelled: Include cancelled events
        include_hidden: Include hidden events
        include_archived: Include archived events (where end_time has passed)
        start_date: Filter events starting after this date
        end_date: Filter events starting before this date
        search: Search in heading and description
        order_by: Field to order by (start_time, created_time, heading)
        order_desc: Order descending if True
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated list of events
    """
    # Build filters
    filters = EventFilters(
        event_type=event_type,
        include_cancelled=include_cancelled,
        include_hidden=include_hidden,
        include_archived=include_archived,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )

    # Get events
    events, total = await EventService.get_all(
        db,
        filters=filters,
        skip=skip,
        limit=limit,
        order_by=order_by,
        order_desc=order_desc,
    )

    return EventListResponse(
        events=events,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/stats", response_model=EventStats)
async def get_event_statistics(
    event_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
):
    """
    Get event statistics

    Args:
        event_type: Filter by event type
        start_date: Filter events starting after this date
        end_date: Filter events starting before this date
        db: Database session
        current_user: Current authenticated user

    Returns:
        Event statistics
    """
    # Build filters
    filters = EventFilters(
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
    )

    stats = await EventService.get_statistics(db, filters=filters)

    return EventStats(**stats)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
):
    """
    Get event by ID

    Args:
        event_id: Event ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Event details

    Raises:
        HTTPException: If event not found
    """
    event = await EventService.get_by_id(db, event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    return event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    update_data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    spond_service: SpondService = Depends(get_spond_service),
):
    """
    Update an event

    Args:
        event_id: Event ID
        update_data: Update data
        db: Database session
        current_user: Current authenticated user
        spond_service: Spond service instance

    Returns:
        Updated event

    Raises:
        HTTPException: If update fails
    """
    try:
        event = await EventService.update(
            db,
            event_id,
            update_data,
            spond_service=spond_service
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        await db.commit()
        return event

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update event: {str(e)}"
        )


@router.post("/{event_id}/push-to-spond", response_model=EventResponse)
async def push_event_to_spond(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    spond_service: SpondService = Depends(get_spond_service),
):
    """
    Manually push a local or pending event to Spond

    Args:
        event_id: Event ID
        db: Database session
        current_user: Current authenticated user
        spond_service: Spond service instance

    Returns:
        Updated event with sync status

    Raises:
        HTTPException: If event not found or sync fails
    """
    try:
        event = await EventService.push_to_spond(
            db,
            event_id,
            spond_service
        )

        await db.commit()
        return event

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to push event to Spond: {str(e)}"
        )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
):
    """
    Delete an event from database (local only, not from Spond)

    Args:
        event_id: Event ID
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If event not found
    """
    success = await EventService.delete(db, event_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    await db.commit()


@router.get("/{event_id}/attendance")
async def get_event_attendance(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    spond_service: SpondService = Depends(get_spond_service),
):
    """
    Export event attendance as Excel file

    Args:
        event_id: Event ID
        db: Database session
        current_user: Current authenticated user
        spond_service: Spond service instance

    Returns:
        Excel file

    Raises:
        HTTPException: If event not found or export fails
    """
    try:
        xlsx_data = await EventService.get_attendance_export(
            db,
            event_id,
            spond_service
        )

        # Get event for filename
        event = await EventService.get_by_id(db, event_id)
        filename = f"attendance_{event.heading.replace(' ', '_')}_{event.start_time.strftime('%Y%m%d')}.xlsx"

        return Response(
            content=xlsx_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export attendance: {str(e)}"
        )


@router.put("/{event_id}/responses", response_model=EventResponse)
async def update_event_response(
    event_id: int,
    response_data: EventResponseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    spond_service: SpondService = Depends(get_spond_service),
):
    """
    Update a user's response to an event

    Args:
        event_id: Event ID
        response_data: Response update data
        db: Database session
        current_user: Current authenticated user
        spond_service: Spond service instance

    Returns:
        Updated event

    Raises:
        HTTPException: If update fails
    """
    try:
        event = await EventService.update_response(
            db,
            event_id,
            response_data.user_id,
            response_data.response_type,
            spond_service
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        await db.commit()
        return event

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update response: {str(e)}"
        )
