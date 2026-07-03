"""Background automatic crawl scheduler."""

from __future__ import annotations

import asyncio
import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def _scheduler_loop() -> None:
    interval_hours = settings.crawl_auto_interval_hours
    startup_delay = 120.0
    await asyncio.sleep(startup_delay)

    while True:
        try:
            from app.routers.crawl import _run_crawl_sync

            logger.info("Automatic crawl starting (interval=%sh)", interval_hours)
            await asyncio.to_thread(_run_crawl_sync, False, False, True)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Automatic crawl failed")

        await asyncio.sleep(max(interval_hours, 0.5) * 3600)


def start_crawl_scheduler() -> asyncio.Task | None:
    interval_hours = settings.crawl_auto_interval_hours
    if interval_hours <= 0:
        logger.info("Automatic crawl disabled (CRAWL_AUTO_INTERVAL_HOURS=%s)", interval_hours)
        return None
    logger.info("Automatic crawl enabled — every %s hours", interval_hours)
    return asyncio.create_task(_scheduler_loop())
