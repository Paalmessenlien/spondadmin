"""
Scheduler API endpoints for managing background synchronization tasks
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.models.admin import Admin
from app.services.scheduler_service import get_scheduler, SchedulerService

logger = logging.getLogger(__name__)

router = APIRouter()


class JobInfo(BaseModel):
    """Schema for scheduled job information"""
    id: str
    name: str
    next_run: str | None
    trigger: str


class JobTriggerResponse(BaseModel):
    """Schema for job trigger response"""
    message: str
    job_id: str


@router.get("/jobs", response_model=List[JobInfo])
async def list_scheduled_jobs(
    current_user: Admin = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler),
):
    """
    List all scheduled background synchronization jobs

    Returns:
        List of scheduled jobs with their information
    """
    try:
        jobs = scheduler.get_jobs()
        return jobs
    except Exception as e:
        logger.error(f"Failed to list scheduled jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scheduled jobs: {str(e)}"
        )


@router.post("/jobs/{job_id}/trigger", response_model=JobTriggerResponse)
async def trigger_job(
    job_id: str,
    current_user: Admin = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler),
):
    """
    Manually trigger a scheduled job to run immediately

    Args:
        job_id: ID of the job to trigger (sync_events, sync_groups, sync_members)

    Returns:
        Success message with job ID
    """
    try:
        scheduler.trigger_job(job_id)
        return JobTriggerResponse(
            message=f"Job '{job_id}' has been triggered and will run shortly",
            job_id=job_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to trigger job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger job: {str(e)}"
        )


@router.get("/status")
async def get_scheduler_status(
    current_user: Admin = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler),
):
    """
    Get the current status of the background scheduler

    Returns:
        Scheduler status and statistics
    """
    try:
        jobs = scheduler.get_jobs()
        return {
            "running": scheduler._is_running,
            "total_jobs": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scheduler status: {str(e)}"
        )
