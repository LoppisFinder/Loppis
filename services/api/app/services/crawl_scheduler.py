"""Background automatic crawl scheduler."""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


async def _scheduler_loop() -> None:
    startup_delay = 120.0
    await asyncio.sleep(startup_delay)

    while True:
        interval_hours = 6.0
        auto_enabled = True
        try:
            from app.database import async_session
            from app.services.crawl_admin import get_crawl_settings

            async with async_session() as db:
                settings = await get_crawl_settings(db)
                interval_hours = settings.interval_hours
                auto_enabled = settings.auto_enabled
        except Exception:
            logger.exception("Could not load crawl settings")

        if auto_enabled and interval_hours > 0:
            try:
                from app.routers.crawl import _running, start_crawl_job

                if not _running:
                    logger.info("Automatic crawl starting (interval=%sh)", interval_hours)
                    await asyncio.to_thread(start_crawl_job)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Automatic crawl failed")
        else:
            logger.info("Automatic crawl skipped (enabled=%s, interval=%sh)", auto_enabled, interval_hours)

        await asyncio.sleep(max(interval_hours, 0.5) * 3600)


def start_crawl_scheduler() -> asyncio.Task | None:
    logger.info("Automatic crawl scheduler started (reads interval from database)")
    return asyncio.create_task(_scheduler_loop())
