"""
Bunny CDN storage helper — generic object upload/download/delete.

Extracted from BackupService so any feature (database backups, expense receipts,
etc.) can put binary content on the shared Bunny CDN zone and get a public URL
back. Keeps the same auth (AccessKey header) and endpoint-selection logic.
"""
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class CDNNotConfigured(RuntimeError):
    """Raised when a CDN operation is attempted without Bunny credentials."""


class CDNStorageService:
    @staticmethod
    def is_configured() -> bool:
        return bool(settings.BUNNY_STORAGE_API_KEY and settings.BUNNY_STORAGE_ZONE)

    @staticmethod
    def _base_url() -> str:
        region = settings.BUNNY_STORAGE_REGION
        if region:
            return f"https://{region}.storage.bunnycdn.com"
        return "https://storage.bunnycdn.com"

    @staticmethod
    def public_url(path: str) -> str:
        """Public CDN URL for a stored object path (no leading slash)."""
        return f"https://{settings.BUNNY_CDN_HOSTNAME}/{path}"

    @staticmethod
    async def upload_bytes(path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload raw bytes to ``path`` in the storage zone. Returns the public URL.

        ``path`` is the object key within the zone, e.g.
        ``spondadmin/receipts/12/abc_receipt.jpg`` (no leading slash).
        """
        if not CDNStorageService.is_configured():
            raise CDNNotConfigured("Bunny CDN not configured")

        upload_url = f"{CDNStorageService._base_url()}/{settings.BUNNY_STORAGE_ZONE}/{path}"
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.put(
                upload_url,
                content=data,
                headers={
                    "AccessKey": settings.BUNNY_STORAGE_API_KEY,
                    "Content-Type": content_type,
                    "Content-Length": str(len(data)),
                },
            )
            resp.raise_for_status()

        url = CDNStorageService.public_url(path)
        logger.info(f"Uploaded {len(data)} bytes to CDN: {url}")
        return url

    @staticmethod
    async def download_bytes(path: str) -> bytes:
        """Fetch an object's bytes from the storage zone (private, AccessKey).

        Used to serve access-controlled files (e.g. receipts) through the
        backend instead of relying on public CDN URLs — the storage zone is
        not publicly served.
        """
        if not CDNStorageService.is_configured():
            raise CDNNotConfigured("Bunny CDN not configured")
        url = f"{CDNStorageService._base_url()}/{settings.BUNNY_STORAGE_ZONE}/{path}"
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(url, headers={"AccessKey": settings.BUNNY_STORAGE_API_KEY})
            resp.raise_for_status()
            return resp.content

    @staticmethod
    async def delete(path: str) -> None:
        """Delete an object by path. Best-effort: logs and swallows errors."""
        if not CDNStorageService.is_configured():
            return
        delete_url = f"{CDNStorageService._base_url()}/{settings.BUNNY_STORAGE_ZONE}/{path}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.delete(
                    delete_url,
                    headers={"AccessKey": settings.BUNNY_STORAGE_API_KEY},
                )
                resp.raise_for_status()
        except Exception as e:  # noqa: BLE001 - best-effort cleanup
            logger.warning(f"Failed to delete from CDN ({path}): {e}")
