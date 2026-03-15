"""
Reports API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_current_editor_or_above
from app.db.session import get_db
from app.models.admin import Admin
from app.services.report_service import ReportService
from app.schemas.report import (
    ReportCreate,
    ReportUpdate,
    ReportResponse,
    ReportListResponse,
    ReportDataResponse,
)

router = APIRouter()


@router.get("/", response_model=List[ReportListResponse])
async def list_reports(
    show_public: bool = Query(True, description="Include public reports"),
    show_favorites: bool = Query(False, description="Show only favorites"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List reports accessible to the current user
    """
    reports = await ReportService.get_user_reports(
        db,
        admin_id=current_user.id,
        include_public=show_public,
        favorites_only=show_favorites,
        report_type=report_type
    )

    return [
        ReportListResponse(
            id=report.id,
            name=report.name,
            description=report.description,
            report_type=report.report_type,
            is_public=report.is_public,
            is_favorite=report.is_favorite,
            created_by=report.created_by,
            last_generated_at=report.last_generated_at,
            created_at=report.created_at
        )
        for report in reports
    ]


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: ReportCreate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new report
    """
    try:
        report = await ReportService.create(
            db,
            admin_id=current_user.id,
            name=report_data.name,
            description=report_data.description,
            report_type=report_data.report_type,
            configuration=report_data.configuration,
            is_public=report_data.is_public,
            is_favorite=report_data.is_favorite,
        )
        await db.commit()
        return ReportResponse.model_validate(report)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create report: {str(e)}"
        )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific report by ID
    """
    report = await ReportService.get_by_id(db, report_id, admin_id=current_user.id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found or access denied"
        )

    return ReportResponse.model_validate(report)


@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: int,
    report_data: ReportUpdate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a report (only by creator)
    """
    try:
        # Build update dict from non-None fields
        update_data = {
            k: v for k, v in report_data.model_dump(exclude_unset=True).items()
            if v is not None
        }

        report = await ReportService.update(
            db, report_id, current_user.id, **update_data
        )

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found or access denied"
            )

        await db.commit()
        return ReportResponse.model_validate(report)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update report: {str(e)}"
        )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a report (only by creator)
    """
    try:
        success = await ReportService.delete(db, report_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found or access denied"
            )

        await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete report: {str(e)}"
        )


@router.post("/{report_id}/generate", response_model=ReportDataResponse)
async def generate_report(
    report_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate report data
    """
    try:
        # Verify access
        report = await ReportService.get_by_id(db, report_id, admin_id=current_user.id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found or access denied"
            )

        # Generate report
        report_data = await ReportService.generate_report(db, report_id)
        await db.commit()

        return ReportDataResponse(**report_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.get("/{report_id}/export")
async def export_report(
    report_id: int,
    format: str = Query("csv", regex="^(csv|pdf)$"),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export report to CSV (PDF not yet implemented)
    """
    try:
        # Verify access
        report = await ReportService.get_by_id(db, report_id, admin_id=current_user.id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found or access denied"
            )

        if format == "pdf":
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="PDF export not yet implemented"
            )

        # Generate CSV
        csv_data = await ReportService.export_report_csv(db, report_id)
        await db.commit()

        # Return CSV file
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=report_{report_id}.csv"
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export report: {str(e)}"
        )


@router.post("/{report_id}/favorite", response_model=ReportResponse)
async def toggle_favorite(
    report_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle favorite status for a report
    """
    try:
        report = await ReportService.toggle_favorite(db, report_id, current_user.id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found or access denied"
            )

        await db.commit()
        return ReportResponse.model_validate(report)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle favorite: {str(e)}"
        )
