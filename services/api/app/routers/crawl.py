import asyncio
import logging
import os
import sys

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

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


def _run_crawl_sync(include_social: bool, include_search: bool, auto_discover: bool = True) -> CrawlReportOut:
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

        from crawler.runner import run_all_adapters

        _status_message = "Söker automatiskt efter loppis på webben, Facebook och Reddit…"
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
        return _last_report
    except Exception as exc:
        _status_message = f"Fel: {exc}"
        logger.exception("Crawl failed")
        raise
    finally:
        _running = False


@router.get("/status", response_model=CrawlStatusOut)
async def crawl_status():
    return CrawlStatusOut(last_report=_last_report, running=_running, message=_status_message)


@router.post("/run", response_model=CrawlReportOut)
async def run_crawl(
    background_tasks: BackgroundTasks,
    include_social: bool = False,
    include_search: bool = False,
    auto_discover: bool = True,
    sync: bool = False,
):
    """Start gathering loppis from public sources.

    Default (`auto_discover=true`): known calendars + light web search + Facebook/Instagram
    via search + Reddit RSS. Runs every 6h automatically while the API is up.

    - `include_search=true` — deep DuckDuckGo crawl + Blocket (slow, 2–5 min)
    - `include_social=true` — Playwright crawl of Facebook groups / Instagram if configured
    - `auto_discover=false` — only curated calendar sites (fastest)
    - `sync=true` — wait for completion (default: runs in background)
    """
    global _running
    if _running:
        raise HTTPException(status_code=409, detail="Crawl already running")

    if sync:
        return await asyncio.to_thread(_run_crawl_sync, include_social, include_search, auto_discover)

    background_tasks.add_task(_run_crawl_sync, include_social, include_search, auto_discover)
    return CrawlReportOut(
        discovered=0,
        ingested=0,
        skipped=0,
        by_source={},
        errors=["Crawl startad i bakgrunden — poll GET /v1/crawl/status"],
    )


@router.delete("/seed-examples")
async def remove_example_seed_data():
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
