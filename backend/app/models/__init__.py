"""
Database models
"""
from app.models.admin import Admin, UserRole
from app.models.event import Event
from app.models.event_category import EventCategory
from app.models.group import Group
from app.models.member import Member
from app.models.archer_profile import ArcherProfile
from app.models.report import Report
from app.models.sync_history import SyncHistory
from app.models.audit_log import AuditLog
from app.models.competition import Competition
from app.models.competition_result import CompetitionResult
from app.models.archer_statistics import ArcherStatistics
from app.models.archery_record import ArcheryRecord
from app.models.bueskyting_scrape_log import BueskytingScrapeLog
from app.models.unmatched_archer import UnmatchedArcher
from app.models.scraping_config import ScrapingConfig
from app.models.database_backup import DatabaseBackup

__all__ = [
    "Admin",
    "UserRole",
    "Event",
    "EventCategory",
    "Group",
    "Member",
    "ArcherProfile",
    "Report",
    "SyncHistory",
    "AuditLog",
    "Competition",
    "CompetitionResult",
    "ArcherStatistics",
    "ArcheryRecord",
    "BueskytingScrapeLog",
    "UnmatchedArcher",
    "ScrapingConfig",
    "DatabaseBackup",
]
