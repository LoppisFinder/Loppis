import asyncio
import logging
import os
import sys

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/crawl", tags=["crawl"])


class CrawlReportOut(BaseModel):
    discovered: int
    ingested: int
    skipped: int
    by_source: dict[str, int]
    errors: list[str]


class CrawlStatusOut(BaseModel):
    last_report: CrawlReportOut | None = None
    running: bool
    message: str | None = None


_last_report: CrawlReportOut | None = None
_running = False
_status_message: str | None = None


def _crawler_paths() -> None:
    crawler_root = os.environ.get("CRAWLER_ROOT")
    if not crawler_root:
        crawler_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "crawler")
        )
    api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    for path in (crawler_root, api_root):
        if path not in sys.path:
            sys.path.insert(0, path)


def _load_crawl_env_from_db() -> tuple[bool, bool, bool]:
    async def _inner():
        from app.database import async_session
        from app.services.crawl_admin import calendar_sites_json, facebook_group_urls, get_crawl_settings, list_feed_sources

        async with async_session() as db:
            settings = await get_crawl_settings(db)
            sources = await list_feed_sources(db)
            sites_json = calendar_sites_json(sources)
            fb_urls = facebook_group_urls(sources)
            return settings, sites_json, fb_urls

    settings, sites_json, fb_urls = asyncio.run(_inner())

    if sites_json and sites_json != "[]":
        os.environ["CRAWL_CALENDAR_SITES_JSON"] = sites_json
    else:
        os.environ.pop("CRAWL_CALENDAR_SITES_JSON", None)

    if fb_urls:
        os.environ["FACEBOOK_GROUP_URLS"] = fb_urls
    else:
        os.environ.pop("FACEBOOK_GROUP_URLS", None)

    return settings.include_social, settings.include_search, settings.auto_discover


def _record_crawl_result(report: CrawlReportOut) -> None:
    async def _inner():
        from app.database import async_session
        from app.services.crawl_admin import bump_data_version

        async with async_session() as db:
            await bump_data_version(db, ingested=report.ingested)

    asyncio.run(_inner())


def start_crawl_job() -> CrawlReportOut:
    global _last_report, _running, _status_message
    _running = True
    _last_report = None
    _status_message = "Crawl startar…"
    try:
        _crawler_paths()
        try:
            from dotenv import load_dotenv
            from pathlib import Path

            env_path = Path(__file__).resolve().parents[2] / ".env"
            if env_path.exists():
                load_dotenv(env_path)
        except ImportError:
            pass

        include_social, include_search, auto_discover = _load_crawl_env_from_db()

        from crawler.runner import run_all_adapters

        _status_message = "Söker efter loppis från konfigurerade källor…"
        logger.info(
            "Starting crawl (social=%s, search=%s, auto_discover=%s)",
            include_social,
            include_search,
            auto_discover,
        )
        report = run_all_adapters(
            include_social=include_social,
            include_search=include_search,
            auto_discover=auto_discover,
        )
        _last_report = CrawlReportOut(**report.to_dict())
        _status_message = f"Klar — {report.ingested} nya loppis sparade"
        logger.info("Crawl finished: %s", report.to_dict())
        _record_crawl_result(_last_report)
        return _last_report
    except Exception as exc:
        _status_message = f"Fel: {exc}"
        logger.exception("Crawl failed")
        raise
    finally:
        _running = False


@router.get("/status", response_model=CrawlStatusOut)
async def crawl_status_public():
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Use GET /v1/admin/crawl/status (admin only)",
    )


def get_crawl_status_data() -> CrawlStatusOut:
    return CrawlStatusOut(last_report=_last_report, running=_running, message=_status_message)


@router.post("/run", response_model=CrawlReportOut)
async def run_crawl():
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Public crawl is disabled. Use POST /v1/admin/crawl/run",
    )


@router.delete("/seed-examples")
async def remove_example_seed_data(_=Depends(require_admin)):
    """Remove demo seed listings so only crawled data remains."""
    from sqlalchemy import delete, select

    from app.database import async_session
    from app.models import Loppis, LoppisSource
    from app.seed import SAMPLES

    seed_urls = [s["source_url"] for s in SAMPLES]

    async with async_session() as db:
        result = await db.execute(
            select(LoppisSource.loppis_id).where(LoppisSource.source_url.in_(seed_urls))
        )
        ids = [row[0] for row in result.all()]
        if ids:
            await db.execute(delete(Loppis).where(Loppis.id.in_(ids)))
            await db.commit()
        return {"removed": len(ids), "seed_urls": seed_urls}
