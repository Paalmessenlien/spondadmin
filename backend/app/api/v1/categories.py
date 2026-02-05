"""
Event Categories API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.admin import Admin
from app.services.category_service import CategoryService
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryWithStats,
    CategoryDistribution,
    BulkCategorizeRequest,
    BulkCategorizeResponse,
)

router = APIRouter()


@router.get("/", response_model=List[CategoryResponse])
async def list_categories(
    active_only: bool = Query(True, description="Show only active categories"),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all event categories
    """
    categories = await CategoryService.get_all(db, active_only=active_only)
    return [CategoryResponse.model_validate(cat) for cat in categories]


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new event category (admin only)
    """
    try:
        category = await CategoryService.create(
            db,
            name=category_data.name,
            description=category_data.description,
            color=category_data.color,
            icon=category_data.icon,
            pattern_rules=category_data.pattern_rules,
            priority=category_data.priority,
            is_active=category_data.is_active,
            is_default=category_data.is_default,
        )
        await db.commit()
        return CategoryResponse.model_validate(category)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create category: {str(e)}"
        )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific category by ID
    """
    category = await CategoryService.get_by_id(db, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found"
        )

    return CategoryResponse.model_validate(category)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a category (admin only)
    """
    try:
        # Build update dict from non-None fields
        update_data = {
            k: v for k, v in category_data.model_dump(exclude_unset=True).items()
            if v is not None
        }

        category = await CategoryService.update(db, category_id, **update_data)

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category {category_id} not found"
            )

        await db.commit()
        return CategoryResponse.model_validate(category)

    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update category: {str(e)}"
        )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a category (admin only)
    Events with this category will be uncategorized
    """
    try:
        success = await CategoryService.delete(db, category_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category {category_id} not found"
            )

        await db.commit()

    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete category: {str(e)}"
        )


@router.post("/bulk-categorize", response_model=BulkCategorizeResponse)
async def bulk_categorize_events(
    request: BulkCategorizeRequest,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk categorize events based on pattern matching rules
    """
    try:
        result = await CategoryService.categorize_events(
            db,
            event_ids=request.event_ids,
            force_recategorize=request.force_recategorize
        )

        await db.commit()

        return BulkCategorizeResponse(**result)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to categorize events: {str(e)}"
        )


@router.get("/statistics/distribution", response_model=List[CategoryDistribution])
async def get_category_statistics(
    group_id: Optional[str] = Query(None, description="Filter by group"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get category distribution statistics
    """
    from datetime import datetime

    # Parse dates
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    stats = await CategoryService.get_category_stats(
        db,
        group_id=group_id,
        start_date=start_dt,
        end_date=end_dt
    )

    return [CategoryDistribution(**stat) for stat in stats]
