"""Admin crawl settings and feed sources."""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CrawlFeedSource, CrawlSettings, FeedSourceKind
from app.privacy import utcnow


async def ensure_crawl_settings(db: AsyncSession) -> CrawlSettings:
    result = await db.execute(select(CrawlSettings).where(CrawlSettings.id == 1))
    settings = result.scalar_one_or_none()
    if settings:
        return settings
    settings = CrawlSettings(id=1, data_version=str(int(utcnow().timestamp() * 1000)))
    db.add(settings)
    await db.commit()
    await db.refresh(settings)
    return settings


async def get_crawl_settings(db: AsyncSession) -> CrawlSettings:
    return await ensure_crawl_settings(db)


async def update_crawl_settings(db: AsyncSession, **fields) -> CrawlSettings:
    settings = await ensure_crawl_settings(db)
    for key, value in fields.items():
        if value is not None and hasattr(settings, key):
            setattr(settings, key, value)
    await db.commit()
    await db.refresh(settings)
    return settings


async def bump_data_version(db: AsyncSession, ingested: int = 0) -> CrawlSettings:
    settings = await ensure_crawl_settings(db)
    settings.data_version = str(int(utcnow().timestamp() * 1000))
    settings.last_run_at = utcnow()
    settings.last_ingested = ingested
    await db.commit()
    await db.refresh(settings)
    return settings


async def list_feed_sources(db: AsyncSession) -> list[CrawlFeedSource]:
    result = await db.execute(select(CrawlFeedSource).order_by(CrawlFeedSource.created_at.desc()))
    return list(result.scalars().all())


async def get_feed_source(db: AsyncSession, source_id: uuid.UUID) -> CrawlFeedSource | None:
    result = await db.execute(select(CrawlFeedSource).where(CrawlFeedSource.id == source_id))
    return result.scalar_one_or_none()


async def create_feed_source(
    db: AsyncSession,
    *,
    name: str,
    url: str,
    kind: FeedSourceKind,
    pages: list[str] | None = None,
) -> CrawlFeedSource:
    source = CrawlFeedSource(name=name.strip(), url=url.strip(), kind=kind, pages=pages or None)
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


async def delete_feed_source(db: AsyncSession, source_id: uuid.UUID) -> bool:
    source = await get_feed_source(db, source_id)
    if not source:
        return False
    await db.delete(source)
    await db.commit()
    return True


async def set_feed_source_enabled(db: AsyncSession, source_id: uuid.UUID, enabled: bool) -> CrawlFeedSource | None:
    source = await get_feed_source(db, source_id)
    if not source:
        return None
    source.enabled = enabled
    await db.commit()
    await db.refresh(source)
    return source


async def count_loppis(db: AsyncSession) -> int:
    from app.models import Loppis

    result = await db.execute(select(func.count()).select_from(Loppis))
    return int(result.scalar_one())


def calendar_sites_json(sources: list[CrawlFeedSource]) -> str:
    sites = []
    for source in sources:
        if source.kind != FeedSourceKind.calendar or not source.enabled:
            continue
        base_url = source.url.rstrip("/")
        sites.append(
            {
                "name": source.name,
                "base_url": base_url,
                "pages": source.pages or ["/"],
                "link_pattern": "loppis|loppmarknad|bakluck|\\d{1,2}/\\d{1,2}",
            }
        )
    return json.dumps(sites, ensure_ascii=False)


def facebook_group_urls(sources: list[CrawlFeedSource]) -> str:
    urls = [
        source.url.strip()
        for source in sources
        if source.kind == FeedSourceKind.facebook_group and source.enabled
    ]
    return ",".join(urls)
