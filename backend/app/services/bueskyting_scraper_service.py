"""
Bueskyting.no scraper service - ports LBSK Crawl4AI scrapers to async SQLAlchemy.

Scrapes competition results, archer statistics, and Norwegian records from
resultat.bueskyting.no and rekord.bueskyting.no.
"""
import asyncio
import logging
import re
import time
from datetime import datetime, date
from typing import Optional, List, Dict

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.competition import Competition
from app.models.competition_result import CompetitionResult
from app.models.archer_statistics import ArcherStatistics
from app.models.archery_record import ArcheryRecord
from app.models.bueskyting_scrape_log import BueskytingScrapeLog
from app.models.unmatched_archer import UnmatchedArcher
from app.models.scraping_config import ScrapingConfig

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Constants for records scraping
# ──────────────────────────────────────────────
RUNDE_IDS = [3, 4, 5, 6, 21, 22, 23, 26, 27, 28]
DIVISIONS = [
    "Recurve", "Compound", "Barebow", "Langbue",
    "Tradisjonell", "Synshemmede", "PsykiskUtviklingshemmet",
]
RUNDE_ID_NAMES = {
    3: "Skandiarunde",
    4: "Norgesrunde",
    5: "1440-runde",
    6: "1/2 1440-runde",
    21: "Norsk kortrunde",
    22: "60 piler 18 meter",
    23: "60 piler 25 meter",
    26: "720-runde",
    27: "30 piler 18 meter",
    28: "2 x 720 runde",
}


# ──────────────────────────────────────────────
# Date parsing helpers
# ──────────────────────────────────────────────
NORWEGIAN_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "mai": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12,
}
ENGLISH_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_norwegian_date(date_str: str) -> Optional[date]:
    """Parse Norwegian date format like '03 jan. 26 2026' or '03 jan. 2026'."""
    if not date_str:
        return None
    try:
        date_str = date_str.lower().strip()
        match = re.match(r"(\d{1,2})\s*(\w{3})\.?\s*(?:\d{2}\s+)?(\d{4})", date_str)
        if match:
            day = int(match.group(1))
            month_str = match.group(2)[:3]
            year = int(match.group(3))
            if month_str in NORWEGIAN_MONTHS:
                return date(year, NORWEGIAN_MONTHS[month_str], day)
        match = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_str)
        if match:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except (ValueError, KeyError):
        pass
    return None


def _parse_record_date(date_str: str) -> Optional[date]:
    """Parse date from records website (English month names, 2-digit year)."""
    if not date_str:
        return None
    try:
        date_str = date_str.strip()
        match = re.match(r"(\d{1,2})\s+(\w{3})\s+(\d{2,4})", date_str, re.IGNORECASE)
        if match:
            day = int(match.group(1))
            month_str = match.group(2).lower()[:3]
            year_str = match.group(3)
            if len(year_str) == 2:
                year_int = int(year_str)
                year = 2000 + year_int if year_int <= 30 else 1900 + year_int
            else:
                year = int(year_str)
            if month_str in ENGLISH_MONTHS:
                return date(year, ENGLISH_MONTHS[month_str], day)
    except (ValueError, KeyError):
        pass
    return None


# ──────────────────────────────────────────────
# Club scraper
# ──────────────────────────────────────────────
async def _scrape_club_async(club_id: str, base_url: str) -> dict:
    """Scrape club page to get list of archers with their external IDs."""
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

    url = f"{base_url}/Club/Detail/{club_id}"
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        if not result.success:
            raise Exception(f"Failed to crawl club page: {result.error_message}")

        markdown = result.markdown or ""

        # Parse club name
        club_name = "Unknown Club"
        headings = re.findall(r"^#{1,2}\s+(.+?)$", markdown, re.MULTILINE)
        for heading in headings:
            heading = heading.strip()
            if not heading or "Norges Bueskytterforbund" in heading:
                continue
            if heading.startswith("[") or heading.startswith("!"):
                continue
            clean_match = re.match(r"([^[\]]+)", heading)
            if clean_match:
                club_name = clean_match.group(1).strip()
                if club_name:
                    break

        # Find inactive section boundary
        inactive_start = len(markdown)
        inactive_match = re.search(r"###?\s*Inaktive", markdown, re.IGNORECASE)
        if inactive_match:
            inactive_start = inactive_match.start()

        # Extract archers
        archers_data = []
        archer_pattern = re.compile(
            r"\[([^\]]+)\]\(https?://[^)]*?/Archer/Details/(\d+)\)",
            re.IGNORECASE,
        )
        for match in archer_pattern.finditer(markdown):
            name = match.group(1).strip()
            archer_id = match.group(2)
            is_active = match.start() < inactive_start
            archers_data.append({
                "external_id": archer_id,
                "name": name,
                "is_active": is_active,
            })

        return {
            "club_name": club_name,
            "external_id": club_id,
            "archers": archers_data,
        }


# ──────────────────────────────────────────────
# Archer results scraper
# ──────────────────────────────────────────────
def _parse_results_from_html(html: str, markdown: str, base_url: str) -> list:
    """Parse results from HTML/markdown content."""
    results = []

    # Extract event URLs from HTML
    event_url_map = {}
    event_rows = re.findall(
        r'onclick="location\.href=\'(/Event/Result/\d+)\'"\s+title="([^"]+)"',
        html,
    )
    for event_path, event_title in event_rows:
        event_url_map[event_title] = f"{base_url}{event_path}"

    # Find the results section in markdown
    results_section_match = re.search(
        r"Dato\s+Navn\s+Runder\s+Klasse\s+Poeng\s+Ranket\s+(.+?)(?:Per runde|Historiske|Copyright|$)",
        markdown, re.DOTALL | re.IGNORECASE,
    )
    if results_section_match:
        results_text = results_section_match.group(1)
        lines = [l.strip() for l in results_text.strip().split("\n") if l.strip()]
        i = 0
        while i + 5 < len(lines):
            date_str = lines[i]
            event_name = lines[i + 1]
            distance = lines[i + 2]
            equipment_class = lines[i + 3]
            score_str = lines[i + 4]
            ranking_str = lines[i + 5]
            if score_str.isdigit() and ranking_str.isdigit():
                parsed_date = parse_norwegian_date(date_str)
                event_url = event_url_map.get(event_name)
                results.append({
                    "event_name": event_name,
                    "distance": distance,
                    "equipment_class": equipment_class,
                    "score": int(score_str),
                    "ranking": int(ranking_str),
                    "date": parsed_date,
                    "event_url": event_url,
                })
                i += 6
            else:
                i += 1
    return results


def _compute_incremental_years(last_scraped: Optional[datetime]) -> Optional[List[int]]:
    """Compute which years need scraping based on last scrape time."""
    current_year = datetime.now().year
    if last_scraped is None:
        return None
    if last_scraped.year < current_year:
        return list(range(last_scraped.year, current_year + 1))
    return [current_year]


async def _scrape_archer_async(
    external_id: str, base_url: str, years_to_scrape: Optional[List[int]] = None,
    crawler=None
) -> dict:
    """Async function to scrape archer data for specified years.

    If a crawler instance is provided, it will be reused instead of creating a new one.
    """
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _get_crawler():
        if crawler is not None:
            yield crawler
        else:
            async with AsyncWebCrawler() as new_crawler:
                yield new_crawler

    url = f"{base_url}/Archer/Details/{external_id}"
    current_year = datetime.now().year
    if years_to_scrape is None:
        years_to_scrape = list(range(2015, current_year + 1))

    all_results = []
    all_statistics = {}
    archer_name = ""

    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with _get_crawler() as c:
        result = await asyncio.wait_for(c.arun(url=url, config=config), timeout=30)
        if not result.success:
            raise Exception(f"Failed to crawl archer page: {result.error_message}")

        markdown = result.markdown or ""
        html = result.html or ""

        # Extract archer name
        headings = re.findall(r"^###\s+(.+?)$", markdown, re.MULTILINE)
        for heading in headings:
            heading = heading.strip()
            if heading and "Norges Bueskytterforbund" not in heading and not heading.startswith("["):
                archer_name = heading
                break

        # Parse statistics
        stats_match = re.search(
            r"Starter\s+Top\s+3\s+Seire?\s+"
            r"(\d{4})\s+(\d+)\s+(\d+)\s+(\d+)\s+"
            r"Totalt\s+(\d+)\s+(\d+)\s+(\d+)",
            markdown, re.IGNORECASE,
        )
        if stats_match:
            year = int(stats_match.group(1))
            all_statistics[year] = {
                "starts": int(stats_match.group(2)),
                "top3": int(stats_match.group(3)),
                "victories": int(stats_match.group(4)),
            }

        # Parse current year results
        current_results = _parse_results_from_html(html, markdown, base_url)
        all_results.extend(current_results)

        # Scrape historical years
        for year in years_to_scrape:
            if year == current_year:
                continue

            js_code = f"""
            const select = document.getElementById('previousyear');
            if (select) {{
                select.value = '{year}';
                select.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
            """
            year_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                js_code=js_code,
                wait_until="networkidle",
                delay_before_return_html=2.0,
            )

            try:
                year_result = await asyncio.wait_for(
                    c.arun(url=url, config=year_config), timeout=30
                )
                if year_result.success:
                    year_markdown = year_result.markdown or ""
                    year_html = year_result.html or ""

                    year_stats_match = re.search(
                        r"Starter\s+Top\s+3\s+Seire?\s+"
                        r"(\d{4})\s+(\d+)\s+(\d+)\s+(\d+)",
                        year_markdown, re.IGNORECASE,
                    )
                    if year_stats_match:
                        stat_year = int(year_stats_match.group(1))
                        if stat_year not in all_statistics:
                            all_statistics[stat_year] = {
                                "starts": int(year_stats_match.group(2)),
                                "top3": int(year_stats_match.group(3)),
                                "victories": int(year_stats_match.group(4)),
                            }

                    historical_match = re.search(
                        r"Historiske resultat.*?Dato\s+Navn\s+Runder\s+Klasse\s+Poeng\s+Ranket\s+(.+?)(?:Copyright|$)",
                        year_markdown, re.DOTALL | re.IGNORECASE,
                    )
                    if historical_match:
                        hist_text = historical_match.group(1)
                        lines = [l.strip() for l in hist_text.strip().split("\n") if l.strip()]

                        event_url_map = {}
                        event_rows = re.findall(
                            r'onclick="location\.href=\'(/Event/Result/\d+)\'"\s+title="([^"]+)"',
                            year_html,
                        )
                        for event_path, event_title in event_rows:
                            event_url_map[event_title] = f"{base_url}{event_path}"

                        i = 0
                        while i + 5 < len(lines):
                            date_str = lines[i]
                            event_name = lines[i + 1]
                            distance = lines[i + 2]
                            equipment_class = lines[i + 3]
                            score_str = lines[i + 4]
                            ranking_str = lines[i + 5]
                            if score_str.isdigit() and ranking_str.isdigit():
                                parsed_date = parse_norwegian_date(date_str)
                                is_dup = any(
                                    r["event_name"] == event_name and r["score"] == int(score_str)
                                    for r in all_results
                                )
                                if not is_dup:
                                    all_results.append({
                                        "event_name": event_name,
                                        "distance": distance,
                                        "equipment_class": equipment_class,
                                        "score": int(score_str),
                                        "ranking": int(ranking_str),
                                        "date": parsed_date,
                                        "event_url": event_url_map.get(event_name),
                                    })
                                i += 6
                            else:
                                i += 1
            except asyncio.TimeoutError:
                logger.warning(f"Timeout scraping year {year} for archer {external_id}")
            except Exception as e:
                logger.warning(f"Failed to scrape year {year} for archer {external_id}: {e}")

    # Recalculate statistics from results
    scraped_result_years = set()
    for r in all_results:
        if r["date"]:
            scraped_result_years.add(r["date"].year)

    for year in scraped_result_years:
        all_statistics.pop(year, None)

    for r in all_results:
        if r["date"]:
            year = r["date"].year
            if year not in all_statistics:
                all_statistics[year] = {"starts": 0, "top3": 0, "victories": 0}
            all_statistics[year]["starts"] += 1
            if r["ranking"] == 1:
                all_statistics[year]["victories"] += 1
            if r["ranking"] is not None and r["ranking"] <= 3:
                all_statistics[year]["top3"] += 1

    return {
        "external_id": external_id,
        "name": archer_name,
        "statistics": all_statistics,
        "results": all_results,
    }


# ──────────────────────────────────────────────
# Event date scraper
# ──────────────────────────────────────────────
async def _scrape_event_date_async(event_url: str) -> Optional[date]:
    """Scrape event date from an event page."""
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=event_url, config=config)
        if not result.success:
            return None

        markdown = result.markdown or ""
        html = result.html or ""

        for line in markdown.split("\n")[:50]:
            line = line.strip()
            iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", line)
            if iso_match:
                try:
                    parts = iso_match.group(1).split("-")
                    return date(int(parts[0]), int(parts[1]), int(parts[2]))
                except (ValueError, IndexError):
                    continue
            date_match = re.search(r"Dato[:\s]+(.+?)(?:\n|$)", line, re.IGNORECASE)
            if date_match:
                parsed = parse_norwegian_date(date_match.group(1).strip())
                if parsed:
                    return parsed
            date_match = re.search(r"\b(\d{1,2}\s+\w{3}\.?\s+\d{4})\b", line)
            if date_match:
                parsed = parse_norwegian_date(date_match.group(1))
                if parsed:
                    return parsed

        html_date_match = re.search(
            r"<dt[^>]*>Dato</dt>\s*<dd[^>]*>([^<]+)</dd>", html, re.IGNORECASE
        )
        if html_date_match:
            parsed = parse_norwegian_date(html_date_match.group(1).strip())
            if parsed:
                return parsed
    return None


# ──────────────────────────────────────────────
# Records page scraper
# ──────────────────────────────────────────────
async def _scrape_records_page_async(
    rundeid: int, divisjon: str, records_url: str, club_filter: str
) -> List[Dict]:
    """Scrape single records page for given round and division."""
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

    url = f"{records_url}/rekord.php?rundeid={rundeid}&divisjon={divisjon}"
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        if not result.success:
            logger.warning(f"Failed to crawl {url}: {result.error_message}")
            return []

        markdown = result.markdown or ""
        records = []
        lines = markdown.split("\n")
        current_category = None
        current_round_type = None

        for i, line in enumerate(lines):
            line = line.strip()

            if line.startswith("**") and "**" in line[2:]:
                current_round_type = line.strip("*").strip()
                continue

            category_match = re.search(
                r"(Herrer|Damer|Jenter|Gutter|Mix\d?)\s+(Senior|U21|U18|U16|50\+?)",
                line, re.IGNORECASE,
            )
            if category_match:
                current_category = f"{category_match.group(1)} {category_match.group(2)}"
                continue

            # Team records
            team_match = re.search(
                r"Lag:\s*\|?\s*([^|]+?)\s*\|?\s*(\d+)\s*\|?\s*(\d{1,2}\s+\w{3}\s+\d{2})",
                line,
            )
            if team_match:
                club_name = team_match.group(1).strip()
                score = int(team_match.group(2).strip())
                date_str = team_match.group(3).strip()
                if club_filter.lower() in club_name.lower():
                    record_date = _parse_record_date(date_str)
                    if record_date:
                        team_members = None
                        for j in range(i + 1, min(i + 3, len(lines))):
                            next_line = lines[j].strip()
                            members_match = re.search(r"v/(.+?)(?:\s*\||\s*$)", next_line)
                            if members_match:
                                team_members = members_match.group(1).strip()
                                break
                        records.append({
                            "record_type": "team",
                            "name": None,
                            "team_members": team_members,
                            "division": divisjon,
                            "category": current_category or "Unknown",
                            "round_type": current_round_type or RUNDE_ID_NAMES.get(rundeid, f"Round {rundeid}"),
                            "distance": None,
                            "score": score,
                            "date": record_date,
                        })
                continue

            # Individual records
            record_match = re.search(
                r"(\d+m|Total):\s*\|\s*([^,]+),\s*([^|]+)\s*\|\s*(\d+)\s*\|\s*([^|]+)\s*\|",
                line,
            )
            if record_match and club_filter.lower() in record_match.group(3).lower():
                distance = record_match.group(1).strip()
                name = record_match.group(2).strip()
                score = int(record_match.group(4).strip())
                date_str = record_match.group(5).strip()
                if any(kw in name.lower() for kw in ["total:", "totalt", "sum:", "average:"]):
                    continue
                if "|" in name or ":" in name:
                    continue
                record_date = _parse_record_date(date_str)
                if not record_date:
                    continue
                records.append({
                    "record_type": "individual",
                    "name": name,
                    "team_members": None,
                    "division": divisjon,
                    "category": current_category or "Unknown",
                    "round_type": current_round_type or RUNDE_ID_NAMES.get(rundeid, f"Round {rundeid}"),
                    "distance": distance,
                    "score": score,
                    "date": record_date,
                })

        return records


# ──────────────────────────────────────────────
# Main service class
# ──────────────────────────────────────────────
class BueskytingScraperService:
    """Service for scraping competition data from bueskyting.no"""

    @staticmethod
    async def _create_log(
        db: AsyncSession, scrape_type: str, status: str = "running", **kwargs
    ) -> BueskytingScrapeLog:
        now = datetime.utcnow()
        log = BueskytingScrapeLog(
            scrape_type=scrape_type,
            status=status,
            items_found=kwargs.get("items_found", 0),
            items_created=kwargs.get("items_created", 0),
            items_updated=kwargs.get("items_updated", 0),
            error_message=kwargs.get("error_message"),
            details=kwargs.get("details"),
            created_at=now,
        )
        db.add(log)
        await db.flush()
        return log

    @staticmethod
    async def scrape_club(db: AsyncSession, config: ScrapingConfig) -> dict:
        """Scrape club page and update unmatched archers list."""
        log = await BueskytingScraperService._create_log(db, "club")

        try:
            data = await _scrape_club_async(config.club_id, config.base_url)
            archers = data["archers"]

            added = 0
            updated = 0
            for archer_data in archers:
                ext_id = str(archer_data["external_id"])
                result = await db.execute(
                    select(UnmatchedArcher).where(UnmatchedArcher.bueskyting_id == ext_id)
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    # Check if already matched via ArcherProfile
                    from app.models.archer_profile import ArcherProfile
                    profile_result = await db.execute(
                        select(ArcherProfile).where(ArcherProfile.bueskyting_id == ext_id)
                    )
                    if profile_result.scalar_one_or_none():
                        continue  # Already matched

                    now = datetime.utcnow()
                    unmatched = UnmatchedArcher(
                        bueskyting_id=ext_id,
                        name=archer_data["name"],
                        is_active=archer_data["is_active"],
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(unmatched)
                    added += 1
                else:
                    existing.name = archer_data["name"]
                    existing.is_active = archer_data["is_active"]
                    existing.updated_at = datetime.utcnow()
                    updated += 1

            log.status = "completed"
            log.items_found = len(archers)
            log.items_created = added
            log.items_updated = updated

            await db.flush()
            return {
                "club_name": data["club_name"],
                "archers_total": len(archers),
                "archers_added": added,
                "archers_updated": updated,
            }
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            await db.flush()
            raise

    @staticmethod
    async def scrape_archer(
        db: AsyncSession, external_id: str, config: ScrapingConfig,
        mode: str = "incremental", crawler=None
    ) -> dict:
        """Scrape a single archer's results and statistics.

        If a crawler instance is provided, it will be reused instead of creating a new one.
        """
        years = None
        if mode == "incremental":
            # Check last scrape for this archer
            result = await db.execute(
                select(BueskytingScrapeLog)
                .where(
                    BueskytingScrapeLog.scrape_type == "archer",
                    BueskytingScrapeLog.status == "completed",
                    BueskytingScrapeLog.details.isnot(None),
                )
                .order_by(BueskytingScrapeLog.created_at.desc())
                .limit(1)
            )
            last_log = result.scalar_one_or_none()
            if last_log:
                years = _compute_incremental_years(last_log.created_at)

        data = await _scrape_archer_async(external_id, config.base_url, years, crawler=crawler)

        # Store results
        results_added = 0
        now = datetime.utcnow()
        for result_data in data["results"]:
            # Check for duplicates
            existing_q = await db.execute(
                select(CompetitionResult).where(
                    CompetitionResult.bueskyting_archer_id == external_id,
                    CompetitionResult.event_name == result_data["event_name"],
                    CompetitionResult.score == result_data["score"],
                )
            )
            existing = existing_q.scalar_one_or_none()
            if existing:
                if result_data["date"] and not existing.date:
                    existing.date = result_data["date"]
                if result_data.get("event_url") and not existing.event_url:
                    existing.event_url = result_data["event_url"]
                continue

            # Find or create competition
            competition_id = None
            if result_data["event_name"] and result_data["date"]:
                comp_q = await db.execute(
                    select(Competition).where(
                        Competition.name == result_data["event_name"],
                        Competition.date == result_data["date"],
                    )
                )
                comp = comp_q.scalar_one_or_none()
                if not comp:
                    comp = Competition(
                        name=result_data["event_name"],
                        date=result_data["date"],
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(comp)
                    await db.flush()
                competition_id = comp.id

            # Look up spond_id if archer is matched
            spond_id = None
            from app.models.archer_profile import ArcherProfile
            profile_q = await db.execute(
                select(ArcherProfile.spond_id).where(
                    ArcherProfile.bueskyting_id == external_id
                )
            )
            profile_row = profile_q.first()
            if profile_row:
                spond_id = profile_row[0]

            new_result = CompetitionResult(
                spond_id=spond_id,
                archer_name=data["name"],
                bueskyting_archer_id=external_id,
                competition_id=competition_id,
                event_name=result_data["event_name"],
                distance=result_data["distance"],
                equipment_class=result_data["equipment_class"],
                score=result_data["score"],
                ranking=result_data["ranking"],
                date=result_data["date"],
                event_url=result_data.get("event_url"),
                created_at=now,
                updated_at=now,
            )
            db.add(new_result)
            results_added += 1

        # Store statistics
        stats_updated = 0
        for year, stats in data["statistics"].items():
            if year == 0:
                continue  # Skip career totals
            existing_q = await db.execute(
                select(ArcherStatistics).where(
                    ArcherStatistics.bueskyting_archer_id == external_id,
                    ArcherStatistics.year == year,
                )
            )
            existing_stat = existing_q.scalar_one_or_none()

            spond_id = None
            profile_q = await db.execute(
                select(ArcherProfile.spond_id).where(
                    ArcherProfile.bueskyting_id == external_id
                )
            )
            profile_row = profile_q.first()
            if profile_row:
                spond_id = profile_row[0]

            if existing_stat:
                existing_stat.starts = stats["starts"]
                existing_stat.top3 = stats["top3"]
                existing_stat.victories = stats["victories"]
                existing_stat.updated_at = now
            else:
                new_stat = ArcherStatistics(
                    spond_id=spond_id,
                    bueskyting_archer_id=external_id,
                    archer_name=data["name"],
                    year=year,
                    starts=stats["starts"],
                    top3=stats["top3"],
                    victories=stats["victories"],
                    created_at=now,
                    updated_at=now,
                )
                db.add(new_stat)
            stats_updated += 1

        await db.flush()
        return {
            "archer_name": data["name"],
            "external_id": external_id,
            "results_added": results_added,
            "total_results_scraped": len(data["results"]),
            "stats_updated": stats_updated,
        }

    @staticmethod
    async def scrape_full(
        db: AsyncSession, config: ScrapingConfig, mode: str = "incremental"
    ) -> dict:
        """Run a full scrape: club + all active archers.

        Uses a single shared browser instance and commits after each archer
        so partial progress is saved and DB locks are released between archers.
        """
        from crawl4ai import AsyncWebCrawler

        log = await BueskytingScraperService._create_log(db, "full")
        await db.commit()  # Commit the "running" log immediately

        try:
            # Scrape club first
            club_result = await BueskytingScraperService.scrape_club(db, config)
            await db.commit()

            # Get all unmatched active archers + matched archers
            unmatched_q = await db.execute(
                select(UnmatchedArcher).where(
                    UnmatchedArcher.is_active == True,
                    UnmatchedArcher.dismissed == False,
                )
            )
            unmatched = unmatched_q.scalars().all()

            # Also get matched archer bueskyting_ids
            from app.models.archer_profile import ArcherProfile
            matched_q = await db.execute(
                select(ArcherProfile.bueskyting_id).where(
                    ArcherProfile.bueskyting_id.isnot(None)
                )
            )
            matched_ids = [row[0] for row in matched_q.all()]

            all_archer_ids = [a.bueskyting_id for a in unmatched] + matched_ids
            archer_results = []
            errors = []

            # Reuse a single browser instance for all archers
            async with AsyncWebCrawler() as shared_crawler:
                for ext_id in all_archer_ids:
                    try:
                        result = await BueskytingScraperService.scrape_archer(
                            db, ext_id, config, mode, crawler=shared_crawler
                        )
                        archer_results.append(result)
                        # Commit after each archer so partial progress is saved
                        await db.commit()
                        await asyncio.sleep(1.0)  # Rate limiting
                    except Exception as e:
                        errors.append({"archer_id": ext_id, "error": str(e)})
                        logger.error(f"Failed to scrape archer {ext_id}: {e}")
                        await db.rollback()

            # Run auto-matching after scraping
            from app.services.archer_matching_service import ArcherMatchingService
            await ArcherMatchingService.auto_match_archers(db)

            log.status = "completed"
            log.items_found = len(all_archer_ids)
            log.items_created = sum(r.get("results_added", 0) for r in archer_results)
            log.details = {
                "club": club_result,
                "archers_scraped": len(archer_results),
                "errors": errors,
                "mode": mode,
            }

            config.last_results_scrape = datetime.utcnow()
            await db.commit()

            return {
                "club": club_result,
                "archers_scraped": len(archer_results),
                "results_added": sum(r.get("results_added", 0) for r in archer_results),
                "errors": len(errors),
            }
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            await db.commit()
            raise

    @staticmethod
    async def scrape_records(db: AsyncSession, config: ScrapingConfig) -> dict:
        """Scrape all Norwegian archery records for the configured club."""
        log = await BueskytingScraperService._create_log(db, "records")

        try:
            # Determine club filter from club name
            club_data = await _scrape_club_async(config.club_id, config.base_url)
            club_filter = club_data["club_name"]

            all_records = []
            for rundeid in RUNDE_IDS:
                for divisjon in DIVISIONS:
                    try:
                        records = await _scrape_records_page_async(
                            rundeid, divisjon, config.records_url, club_filter
                        )
                        all_records.extend(records)
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.warning(f"Error scraping {divisjon} round {rundeid}: {e}")

            # Mark existing records as not current
            await db.execute(
                update(ArcheryRecord).values(is_current=False)
            )

            now = datetime.utcnow()
            created = 0
            updated = 0

            for record_data in all_records:
                record_type = record_data.get("record_type", "individual")

                # Check for existing record
                existing_q = await db.execute(
                    select(ArcheryRecord).where(
                        ArcheryRecord.division == record_data["division"],
                        ArcheryRecord.category == record_data["category"],
                        ArcheryRecord.distance == record_data["distance"],
                        ArcheryRecord.round_type == record_data["round_type"],
                        ArcheryRecord.record_type == record_type,
                    )
                )
                existing = existing_q.scalar_one_or_none()

                # Look up spond_id for individual records
                spond_id = None
                if record_data["name"]:
                    from app.models.archer_profile import ArcherProfile
                    from app.models.member import Member
                    # Try to find by name match through members
                    member_q = await db.execute(
                        select(Member.spond_id).where(
                            func.lower(
                                func.concat(Member.first_name, " ", Member.last_name)
                            ) == func.lower(record_data["name"])
                        )
                    )
                    member_row = member_q.first()
                    if member_row:
                        spond_id = member_row[0]

                team_members_data = None
                if record_data.get("team_members"):
                    team_members_data = {"members": record_data["team_members"]}

                if existing:
                    existing.score = record_data["score"]
                    existing.record_date = record_data["date"]
                    existing.archer_name = record_data["name"]
                    existing.spond_id = spond_id
                    existing.team_members = team_members_data
                    existing.is_current = True
                    existing.updated_at = now
                    updated += 1
                else:
                    record = ArcheryRecord(
                        spond_id=spond_id,
                        archer_name=record_data["name"],
                        division=record_data["division"],
                        category=record_data["category"],
                        distance=record_data["distance"],
                        round_type=record_data["round_type"],
                        score=record_data["score"],
                        record_date=record_data["date"],
                        record_type=record_type,
                        team_members=team_members_data,
                        is_current=True,
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(record)
                    created += 1

            # Delete stale records
            await db.execute(
                delete(ArcheryRecord).where(ArcheryRecord.is_current == False)
            )

            log.status = "completed"
            log.items_found = len(all_records)
            log.items_created = created
            log.items_updated = updated

            config.last_records_scrape = now
            await db.flush()

            return {
                "total_records": len(all_records),
                "created": created,
                "updated": updated,
            }
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            await db.flush()
            raise

    @staticmethod
    async def scrape_event_dates(db: AsyncSession, config: ScrapingConfig) -> dict:
        """Fill missing dates for results with event URLs."""
        log = await BueskytingScraperService._create_log(db, "event_dates")

        try:
            results_q = await db.execute(
                select(CompetitionResult).where(
                    CompetitionResult.date.is_(None),
                    CompetitionResult.event_url.isnot(None),
                )
            )
            results_to_update = results_q.scalars().all()

            updated = 0
            failed = 0
            scraped_urls: Dict[str, Optional[date]] = {}

            for result_obj in results_to_update:
                event_url = result_obj.event_url
                if event_url in scraped_urls:
                    event_date = scraped_urls[event_url]
                else:
                    try:
                        event_date = await _scrape_event_date_async(event_url)
                        scraped_urls[event_url] = event_date
                    except Exception:
                        scraped_urls[event_url] = None
                        event_date = None

                if event_date:
                    result_obj.date = event_date
                    updated += 1
                else:
                    failed += 1

            log.status = "completed"
            log.items_found = len(results_to_update)
            log.items_updated = updated
            log.details = {"failed": failed}
            await db.flush()

            return {
                "total": len(results_to_update),
                "updated": updated,
                "failed": failed,
            }
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            await db.flush()
            raise
