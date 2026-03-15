"""
Backup Pydantic schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BackupCreateRequest(BaseModel):
    backup_type: str = "manual"


class BackupResponse(BaseModel):
    id: int
    filename: str
    file_path: Optional[str] = None
    cdn_url: Optional[str] = None
    backup_type: str
    size_bytes: Optional[int] = None
    status: str
    backup_metadata: Optional[dict] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BackupListResponse(BaseModel):
    backups: list[BackupResponse]
    total: int
