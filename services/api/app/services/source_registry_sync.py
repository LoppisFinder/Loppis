"""Import crawl sources from crawler/data/discovered_sources.json into the database."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CrawlFeedSource, FeedSourceKind


def _registry_path() -> Path:
    crawler_root = os.environ.get("CRAWLER_ROOT")
    if crawler_root:
        return Path(crawler_root) / "data" / "discovered_sources.json"
    return (
        Path(__file__).resolve().parents[3]
        / "crawler"
        / "data"
        / "discovered_sources.json"
    )


def _normalize_base_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return url.rstrip("/")
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return f"{parsed.scheme.lower()}://{host}"


def load_registry_sources() -> tuple[list[dict], list[str]]:
    path = _registry_path()
    if not path.exists():
        return [], []

    data = json.loads(path.read_text(encoding="utf-8"))
    calendar_by_url: dict[str, dict] = {}

    for site in data.get("calendar_sites", []):
        base_url = site.get("base_url", "").strip()
        if not base_url:
            continue
        key = _normalize_base_url(base_url)
        pages = [p for p in (site.get("pages") or ["/"]) if p]
        name = site.get("name") or urlparse(base_url).netloc.replace("www.", "")

        if key in calendar_by_url:
            existing_pages = set(calendar_by_url[key]["pages"])
            existing_pages.update(pages)
            calendar_by_url[key]["pages"] = sorted(existing_pages)
            continue

        calendar_by_url[key] = {
            "name": name,
            "url": base_url.rstrip("/"),
            "pages": pages,
        }

    # Prefer loppistajm calendar pages from curated config
    for key, site in list(calendar_by_url.items()):
        if "loppistajm.se" in key:
            pages = set(site["pages"])
            pages.update(["/", "/kalender.html"])
            site["pages"] = sorted(pages)
            site["name"] = "loppistajm"
            site["url"] = "https://loppistajm.se"

    facebook_groups = list(dict.fromkeys(data.get("facebook_groups") or []))
    return list(calendar_by_url.values()), facebook_groups


async def sync_registry_sources(db: AsyncSession) -> dict[str, int]:
    """Merge discovered_sources.json into crawl_feed_source (idempotent)."""
    calendar_sites, facebook_groups = load_registry_sources()
    added = 0
    updated = 0

    result = await db.execute(select(CrawlFeedSource))
    existing = { _normalize_base_url(row.url): row for row in result.scalars().all() }

    for site in calendar_sites:
        key = _normalize_base_url(site["url"])
        pages = site["pages"] or ["/"]
        if key in existing:
            row = existing[key]
            merged_pages = sorted(set(row.pages or []) | set(pages))
            if merged_pages != sorted(set(row.pages or [])):
                row.pages = merged_pages
                updated += 1
            continue
        db.add(
            CrawlFeedSource(
                name=site["name"],
                url=site["url"],
                kind=FeedSourceKind.calendar,
                pages=pages,
                enabled=True,
            )
        )
        added += 1

    for group_url in facebook_groups:
        key = group_url.split("?")[0].rstrip("/")
        if key in existing:
            continue
        name = urlparse(group_url).path.split("/")[-1] or "facebook-group"
        db.add(
            CrawlFeedSource(
                name=name,
                url=key,
                kind=FeedSourceKind.facebook_group,
                enabled=True,
            )
        )
        added += 1

    await db.commit()
    return {"added": added, "updated": updated, "calendar_sites": len(calendar_sites), "facebook_groups": len(facebook_groups)}
