"""
Background scheduler service for automated synchronization
"""
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.spond_service import get_spond_service
from app.services.event_sync_service import EventSyncService
from app.services.group_sync_service import GroupSyncService
from app.services.member_sync_service import MemberSyncService

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service for managing background scheduled tasks
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._is_running = False

    async def start(self):
        """Start the scheduler"""
        if self._is_running:
            logger.warning("Scheduler is already running")
            return

        # Add scheduled jobs
        await self._add_scheduled_jobs()

        # Start the scheduler
        self.scheduler.start()
        self._is_running = True
        logger.info("Background scheduler started")

    async def stop(self):
        """Stop the scheduler"""
        if not self._is_running:
            return

        self.scheduler.shutdown(wait=True)
        self._is_running = False
        logger.info("Background scheduler stopped")

    async def _add_scheduled_jobs(self):
        """Add all scheduled synchronization jobs"""

        # Events sync job
        if settings.SYNC_EVENTS_ENABLED:
            interval_minutes = settings.SYNC_EVENTS_INTERVAL_MINUTES
            self.scheduler.add_job(
                self._sync_events_job,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id="sync_events",
                name="Sync Events from Spond",
                replace_existing=True,
                max_instances=1,
            )
            logger.info(f"Scheduled events sync every {interval_minutes} minutes")

        # Groups sync job
        if settings.SYNC_GROUPS_ENABLED:
            interval_minutes = settings.SYNC_GROUPS_INTERVAL_MINUTES
            self.scheduler.add_job(
                self._sync_groups_job,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id="sync_groups",
                name="Sync Groups from Spond",
                replace_existing=True,
                max_instances=1,
            )
            logger.info(f"Scheduled groups sync every {interval_minutes} minutes")

        # Members sync job
        if settings.SYNC_MEMBERS_ENABLED:
            interval_minutes = settings.SYNC_MEMBERS_INTERVAL_MINUTES
            self.scheduler.add_job(
                self._sync_members_job,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id="sync_members",
                name="Sync Members from Spond",
                replace_existing=True,
                max_instances=1,
            )
            logger.info(f"Scheduled members sync every {interval_minutes} minutes")

    async def _sync_events_job(self):
        """Background job to sync events"""
        logger.info("Starting scheduled events sync")
        try:
            async with AsyncSessionLocal() as db:
                spond_service = get_spond_service()
                stats = await EventSyncService.sync_events(
                    db,
                    spond_service,
                    max_events=settings.SYNC_EVENTS_MAX_EVENTS,
                )
                await db.commit()
                logger.info(
                    f"Scheduled events sync completed: "
                    f"{stats['created']} created, {stats['updated']} updated, "
                    f"{stats['errors']} errors"
                )
        except Exception as e:
            logger.error(f"Scheduled events sync failed: {e}", exc_info=True)

    async def _sync_groups_job(self):
        """Background job to sync groups"""
        logger.info("Starting scheduled groups sync")
        try:
            async with AsyncSessionLocal() as db:
                spond_service = get_spond_service()
                stats = await GroupSyncService.sync_groups(db, spond_service)
                await db.commit()
                logger.info(
                    f"Scheduled groups sync completed: "
                    f"{stats['created']} created, {stats['updated']} updated, "
                    f"{stats['errors']} errors"
                )
        except Exception as e:
            logger.error(f"Scheduled groups sync failed: {e}", exc_info=True)

    async def _sync_members_job(self):
        """Background job to sync members"""
        logger.info("Starting scheduled members sync")
        try:
            async with AsyncSessionLocal() as db:
                spond_service = get_spond_service()
                stats = await MemberSyncService.sync_members(db, spond_service)
                await db.commit()
                logger.info(
                    f"Scheduled members sync completed: "
                    f"{stats['created']} created, {stats['updated']} updated, "
                    f"{stats['errors']} errors"
                )
        except Exception as e:
            logger.error(f"Scheduled members sync failed: {e}", exc_info=True)

    def get_jobs(self):
        """Get all scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        return jobs

    def trigger_job(self, job_id: str):
        """Manually trigger a job"""
        job = self.scheduler.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.modify(next_run_time=datetime.now())
        logger.info(f"Manually triggered job: {job_id}")


# Global scheduler instance
scheduler_service = SchedulerService()


async def get_scheduler() -> SchedulerService:
    """Dependency to get scheduler service"""
    return scheduler_service
