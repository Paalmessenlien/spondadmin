"""
External Event Scraper Service - scrapes upcoming competitions from bueskyting.no terminliste.

Fetches the homepage (terminliste) and individual event detail pages to extract
structured data about upcoming competitions.
"""
import logging
import re
import json
from datetime import datetime, date
from typing import Optional, Dict, List

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.external_event import ExternalEvent
from app.models.scraping_config import ScrapingConfig
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

# Norwegian month names for date parsing
NORWEGIAN_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "mai": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12,
}


def _parse_date(date_str: str) -> Optional[date]:
    """Parse various date formats from bueskyting.no."""
    if not date_str:
        return None
    date_str = date_str.strip()
    try:
        # Try ISO format first: 2026-03-15
        match = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_str)
        if match:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))

        # Try Norwegian format: 15. mar. 2026 or 15 mar 2026
        match = re.match(r"(\d{1,2})\.?\s*(\w{3})\.?\s*(\d{4})", date_str.lower())
        if match:
            day = int(match.group(1))
            month_str = match.group(2)[:3]
            year = int(match.group(3))
            if month_str in NORWEGIAN_MONTHS:
                return date(year, NORWEGIAN_MONTHS[month_str], day)

        # Try dd.mm.yyyy
        match = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", date_str)
        if match:
            return date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
    except (ValueError, KeyError):
        pass
    return None


def _parse_terminliste_date(date_str: str) -> Optional[date]:
    """Parse short date format from terminliste: '19 mar. 26' → 2026-03-19."""
    if not date_str:
        return None
    date_str = date_str.strip().lower()
    # Match: "19 mar. 26" or "19 mar 26"
    match = re.match(r"(\d{1,2})\s+(\w{3})\.?\s+(\d{2})", date_str)
    if match:
        day = int(match.group(1))
        month_str = match.group(2)[:3]
        year_short = int(match.group(3))
        year = 2000 + year_short if year_short < 80 else 1900 + year_short
        if month_str in NORWEGIAN_MONTHS:
            try:
                return date(year, NORWEGIAN_MONTHS[month_str], day)
            except ValueError:
                pass
    # Fallback to general parser
    return _parse_date(date_str)


def _extract_email(text: str) -> Optional[str]:
    """Extract email address from text."""
    if not text:
        return None
    match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
    return match.group(0) if match else None


def _extract_coordinates(html: str) -> tuple[Optional[float], Optional[float]]:
    """Extract latitude/longitude from Google Maps links or embedded data."""
    # Look for coordinates in Google Maps URLs
    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', html)
    if match:
        return float(match.group(1)), float(match.group(2))

    # Look for lat/lng in data attributes or JS
    lat_match = re.search(r'(?:lat|latitude)["\s:=]+(-?\d+\.\d+)', html, re.IGNORECASE)
    lng_match = re.search(r'(?:lng|longitude|lon)["\s:=]+(-?\d+\.\d+)', html, re.IGNORECASE)
    if lat_match and lng_match:
        return float(lat_match.group(1)), float(lng_match.group(1))

    return None, None


class ExternalEventScraperService:
    BASE_URL = "https://resultat.bueskyting.no"

    @staticmethod
    async def scrape_upcoming_events(db: AsyncSession) -> Dict:
        """
        Main entry point: scrape the terminliste from bueskyting.no homepage
        and individual event detail pages.

        Returns dict with scrape statistics.
        """
        stats = {"new": 0, "updated": 0, "unchanged": 0, "errors": 0, "deactivated": 0}

        # Get base URL from scraping config if available
        base_url = ExternalEventScraperService.BASE_URL
        config_result = await db.execute(select(ScrapingConfig).limit(1))
        config = config_result.scalar_one_or_none()
        if config and config.base_url:
            base_url = config.base_url.rstrip("/")

        try:
            # Fetch homepage (terminliste)
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(base_url)
                resp.raise_for_status()
                homepage_html = resp.text

            # Parse event list from homepage
            event_links = ExternalEventScraperService._parse_terminliste(homepage_html, base_url)
            logger.info(f"Found {len(event_links)} events in terminliste")

            for event_info in event_links:
                try:
                    event_id = event_info["event_id"]

                    # Check if already exists
                    existing = await db.execute(
                        select(ExternalEvent).where(
                            ExternalEvent.bueskyting_event_id == event_id
                        )
                    )
                    existing_event = existing.scalar_one_or_none()

                    # Fetch detail page
                    detail_url = f"{base_url}/Event/Details/{event_id}"
                    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                        detail_resp = await client.get(detail_url)
                        detail_resp.raise_for_status()

                    detail_data = ExternalEventScraperService._scrape_event_detail(
                        detail_resp.text, event_id, detail_url
                    )

                    # Merge homepage data with detail data (detail takes precedence)
                    merged = {**event_info, **detail_data}
                    merged.pop("event_id", None)

                    if existing_event:
                        # Update existing
                        changed = False
                        for key, value in merged.items():
                            if hasattr(existing_event, key) and getattr(existing_event, key) != value:
                                if value is not None:
                                    setattr(existing_event, key, value)
                                    changed = True
                        if changed:
                            existing_event.updated_at = datetime.utcnow()
                            stats["updated"] += 1
                        else:
                            stats["unchanged"] += 1
                    else:
                        # Create new
                        new_event = ExternalEvent(
                            bueskyting_event_id=event_id,
                            source_url=detail_url,
                            **{k: v for k, v in merged.items()
                               if k not in ("source_url",) and hasattr(ExternalEvent, k)},
                        )
                        db.add(new_event)
                        stats["new"] += 1

                except Exception as e:
                    logger.error(f"Error scraping event {event_info.get('event_id', '?')}: {e}")
                    stats["errors"] += 1

            # Deactivate events with past dates
            today = date.today()
            past_result = await db.execute(
                select(ExternalEvent).where(
                    ExternalEvent.is_active == True,
                    ExternalEvent.date_end.isnot(None),
                    ExternalEvent.date_end < today,
                )
            )
            for past_event in past_result.scalars().all():
                past_event.is_active = False
                stats["deactivated"] += 1

            await db.flush()
            logger.info(f"Scrape complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Failed to scrape terminliste: {e}")
            raise

    @staticmethod
    def _parse_terminliste(html: str, base_url: str) -> List[Dict]:
        """
        Parse the terminliste (event schedule) from the bueskyting.no homepage.

        The page uses div.fRow.datarows rows with this structure:
          <div class="fRow datarows" onclick="location.href='/Event/Details/2026014'"
               title="Trollvika serien stevne 6 av 6">
            <div class="flexItems flexDate flexDateTitle">
              <div>19 mar. 26</div>          <!-- start date -->
              <div>20 mar. 26</div>          <!-- end date (optional) -->
            </div>
            <div class="flexItems overflowYhidden">
              <div><a href="/Event/Details/2026014">Event Name</a></div>
              <div>Organizer Club</div>
            </div>
            <div class="flexItems flexItemsInfo">
              <div class="nowrap">18 m</div>  <!-- distance -->
              ...
              <span>60 Piler</span>           <!-- format -->
            </div>
          </div>

        Returns list of dicts with basic event info and detail page links.
        """
        soup = BeautifulSoup(html, "html.parser")
        events = []
        seen_ids = set()

        for row in soup.select("div.fRow.datarows"):
            # Extract event ID from onclick attribute
            onclick = row.get("onclick", "")
            match = re.search(r"/Event/Details/(\d+)", onclick)
            if not match:
                # Fallback: try the <a> tag
                link = row.select_one("a[href*='/Event/Details/']")
                if link:
                    match = re.search(r"/Event/Details/(\d+)", link.get("href", ""))
                if not match:
                    continue

            event_id = match.group(1)
            if event_id in seen_ids:
                continue
            seen_ids.add(event_id)

            # Event name from title attribute or <a> text
            name = row.get("title", "")
            if not name:
                link = row.select_one("a[href*='/Event/Details/']")
                if link:
                    name = link.get_text(strip=True)
            if not name:
                continue

            event_info: Dict = {"event_id": event_id, "name": name}

            # Parse dates from .flexDate div
            date_div = row.select_one(".flexDate")
            if date_div:
                date_cells = date_div.select("div")
                if len(date_cells) >= 1:
                    parsed = _parse_terminliste_date(date_cells[0].get_text(strip=True))
                    if parsed:
                        event_info["date_start"] = parsed
                if len(date_cells) >= 2:
                    parsed = _parse_terminliste_date(date_cells[1].get_text(strip=True))
                    if parsed:
                        event_info["date_end"] = parsed

            # Parse organizer from .overflowYhidden div (second child div)
            info_div = row.select_one(".overflowYhidden")
            if info_div:
                children = info_div.select(":scope > div")
                if len(children) >= 2:
                    organizer = children[1].get_text(strip=True)
                    if organizer:
                        event_info["organizer"] = organizer

            # Parse distance from .flexItemsInfo
            info_items = row.select_one(".flexItemsInfo")
            if info_items:
                nowrap = info_items.select_one(".nowrap")
                if nowrap:
                    event_info["distance"] = nowrap.get_text(strip=True)
                format_span = info_items.select_one("span")
                if format_span:
                    event_info["format"] = format_span.get_text(strip=True)

            events.append(event_info)

        return events

    @staticmethod
    def _scrape_event_detail(html: str, event_id: str, source_url: str) -> Dict:
        """
        Scrape structured data from a single event detail page.

        The detail page structure:
          h1.page-title              → event name
          span.sbf-label             → event type ("Nasjonalt stevne", "Norsk mesterskap", etc.)
          .fRow.noHiglight contains multiple .flexItems divs:
            1st .flexItems "Informasjon":
              ul.list-icons with <li> items:
                fa-users     → organizer
                fa-map-marker → location/address
                fa-calendar-alt → dates (ISO: "2026-03-20 - 2026-03-22" or "2026-03-19")
            2nd .flexItems (unnamed):
              ul.list-icons with <li> items using fa-dot-circle-o:
                "Aktiv" / status
                "18 m" / distance
                "2 Distanse / 60 Piler" / format
            3rd .flexItems "Ekstern link":
              ul.list-icons with <li> items:
                "Påmelding" (may have <a>)
                "Informasjon" (may have <a>)
                "Resultater" (may have <a>)
          .preDiv                    → description text

        Returns dict with all available fields.
        """
        soup = BeautifulSoup(html, "html.parser")
        data: Dict = {"source_url": source_url}

        # Event name
        title = soup.select_one("h1.page-title")
        if title:
            data["name"] = title.get_text(strip=True)

        # Event type from label badge
        type_label = soup.select_one("span.sbf-label")
        if type_label:
            data["event_type_raw"] = type_label.get_text(strip=True)

        # Parse the info sections within .fRow.noHiglight
        info_sections = soup.select("div.fRow.noHiglight .flexItems")

        for section in info_sections:
            section_title = section.select_one("h3.title")
            title_text = section_title.get_text(strip=True).lower() if section_title else ""

            list_items = section.select("ul.list-icons > li")

            if title_text == "informasjon" or (not title_text and any(
                li.select_one("i.fa-users, i.fa-map-marker, i.fa-calendar-alt")
                for li in list_items
            )):
                # First section: organizer, location, dates
                for li in list_items:
                    icon = li.select_one("i")
                    if not icon:
                        continue
                    icon_classes = " ".join(icon.get("class", []))
                    text = li.get_text(strip=True)

                    if "fa-users" in icon_classes:
                        data.setdefault("organizer", text)
                    elif "fa-map-marker" in icon_classes:
                        # Full address string, e.g. "Club Name, Street 10, 1234 CITY"
                        data.setdefault("address", text)
                        # Extract location (first part before comma)
                        parts = text.split(",")
                        if parts:
                            data.setdefault("location", parts[0].strip())
                    elif "fa-calendar" in icon_classes:
                        # Dates: "2026-03-20 - 2026-03-22" or "2026-03-19"
                        if " - " in text:
                            date_parts = text.split(" - ")
                            if len(date_parts) == 2:
                                start = _parse_date(date_parts[0].strip())
                                end = _parse_date(date_parts[1].strip())
                                if start:
                                    data["date_start"] = start
                                if end:
                                    data["date_end"] = end
                        else:
                            parsed = _parse_date(text)
                            if parsed:
                                data["date_start"] = parsed

            elif title_text == "ekstern link" or any(
                li.select_one("i.fa-user, i.fa-info-circle, i.fa-list-ol")
                for li in list_items
            ):
                # External links section
                for li in list_items:
                    icon = li.select_one("i")
                    if not icon:
                        continue
                    icon_classes = " ".join(icon.get("class", []))
                    link = li.select_one("a[href]")
                    li_text = li.get_text(strip=True).lower()

                    href = None
                    if link:
                        href = link.get("href", "")
                        if href.startswith("/"):
                            href = f"https://resultat.bueskyting.no{href}"

                    if "fa-user" in icon_classes and "fa-users" not in icon_classes:
                        # Påmelding
                        if href:
                            data.setdefault("registration_url", href)
                    elif "fa-info" in icon_classes:
                        # Informasjon
                        if href:
                            data.setdefault("info_url", href)
                    elif "fa-list" in icon_classes:
                        # Resultater
                        if href:
                            data.setdefault("results_url", href)
                    elif "påmelding" in li_text or "pamelding" in li_text:
                        if href:
                            data.setdefault("registration_url", href)
                    elif "informasjon" in li_text or "info" in li_text:
                        if href:
                            data.setdefault("info_url", href)

            else:
                # Unnamed section with fa-dot-circle-o: status, distance, format
                for li in list_items:
                    icon = li.select_one("i")
                    if not icon:
                        continue
                    icon_classes = " ".join(icon.get("class", []))
                    text = li.get_text(strip=True)

                    if "fa-dot-circle" in icon_classes:
                        # Distinguish between status, distance, and format
                        text_lower = text.lower()
                        if text_lower in ("aktiv", "avlyst", "utsatt", "ferdig"):
                            continue  # Skip status
                        elif re.match(r"^\d+\s*m$", text_lower):
                            data.setdefault("distance", text)
                        else:
                            # Likely format: "2 Distanse / 60 Piler"
                            data.setdefault("format", text)

        # Description from .preDiv
        pre_div = soup.select_one(".preDiv")
        if pre_div:
            desc_text = pre_div.get_text(strip=True)
            if desc_text:
                data["description"] = pre_div.get_text("\n", strip=True)
                # Try to extract email from description
                email = _extract_email(desc_text)
                if email:
                    data.setdefault("contact_email", email)

        # Coordinates from map script
        lat, lng = _extract_coordinates(html)
        if lat and lng:
            data["latitude"] = lat
            data["longitude"] = lng

        return data

    @staticmethod
    async def analyze_event_with_ai(db: AsyncSession, event: ExternalEvent) -> Dict:
        """
        Use AI to classify event type and generate a Norwegian summary.

        Returns dict with ai_event_category, ai_summary.
        """
        # Build context from event data
        event_context = f"""Stevne: {event.name}
Type: {event.event_type_raw or 'Ukjent'}
Dato: {event.date_start} - {event.date_end or ''}
Sted: {event.location or ''} {event.address or ''}
Arrangør: {event.organizer or ''}
Distanse: {event.distance or ''}
Format: {event.format or ''}
Påmeldingsfrist: {event.registration_deadline or ''}
Påmeldingstype: {event.registration_type_raw or ''}
Avgifter: {event.fees or ''}
Beskrivelse: {event.description or 'Ingen beskrivelse tilgjengelig'}"""

        messages = [
            {
                "role": "system",
                "content": """Du er en ekspert på norsk bueskyting og stevner.
Analyser følgende stevneinformasjon og returner et JSON-objekt med:
1. "category": En av "personlig" (skytteren melder seg på selv), "klubb" (klubben må sende påmelding/invitasjon) eller "ukjent" (ikke nok info)
2. "summary": En kort norsk oppsummering (2-3 setninger) av stevnet som er nyttig for en klubbleder

Vurder disse faktorene for klassifisering:
- "personlig": Individuelle kan melde seg på via lenke, Ianseo, eller lignende system
- "klubb": Krever klubbpåmelding, invitasjonsstevne, NM, eller mesterskap der klubben sender lag

Svar KUN med gyldig JSON, ingen annen tekst.""",
            },
            {
                "role": "user",
                "content": event_context,
            },
        ]

        try:
            result = await AIService.chat(
                db,
                messages=messages,
                max_tokens=4096,
                temperature=0.3,
            )

            content = result.get("content", "").strip()

            # Extract JSON from response - handle markdown blocks, reasoning text, etc.
            parsed = None

            # Try direct parse first
            try:
                parsed = json.loads(content)
            except (json.JSONDecodeError, ValueError):
                pass

            # Try extracting from markdown code blocks
            if parsed is None and "```" in content:
                match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
                if match:
                    try:
                        parsed = json.loads(match.group(1).strip())
                    except (json.JSONDecodeError, ValueError):
                        pass

            # Try finding JSON object anywhere in the text (for reasoning models)
            if parsed is None:
                match = re.search(r'\{[^{}]*"category"[^{}]*"summary"[^{}]*\}', content, re.DOTALL)
                if not match:
                    match = re.search(r'\{[^{}]*"summary"[^{}]*"category"[^{}]*\}', content, re.DOTALL)
                if match:
                    try:
                        parsed = json.loads(match.group(0))
                    except (json.JSONDecodeError, ValueError):
                        pass

            if parsed is None:
                raise json.JSONDecodeError("Could not extract JSON from AI response", content, 0)
            category = parsed.get("category", "ukjent")
            summary = parsed.get("summary", "")

            # Validate category
            if category not in ("personlig", "klubb", "ukjent"):
                category = "ukjent"

            # Update event
            event.ai_event_category = category
            event.ai_summary = summary
            event.ai_analyzed_at = datetime.utcnow()
            await db.flush()

            return {
                "event_id": event.id,
                "category": category,
                "summary": summary,
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response for event {event.id}: {e}")
            event.ai_event_category = "ukjent"
            event.ai_summary = "Kunne ikke analysere stevnet automatisk."
            event.ai_analyzed_at = datetime.utcnow()
            await db.flush()
            return {
                "event_id": event.id,
                "category": "ukjent",
                "summary": "Kunne ikke analysere stevnet automatisk.",
                "error": str(e),
            }

        except ValueError as e:
            # AI service not configured
            logger.warning(f"AI analysis skipped for event {event.id}: {e}")
            return {
                "event_id": event.id,
                "error": str(e),
            }
