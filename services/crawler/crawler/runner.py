"""Run all configured crawlers and ingest results."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Demo / seed URLs that must never be re-ingested from social adapters
BLOCKED_SOURCE_URL_PREFIXES = (
    "https://example.com/",
    "https://facebook.com/groups/example",
    "https://facebook.com/events/example",
    "https://instagram.com/explore/tags/",
    "https://reddit.com/r/sweden/comments/example",
    "user://",
)


@dataclass
class CrawlReport:
    discovered: int = 0
    ingested: int = 0
    skipped: int = 0
    by_source: dict[str, int] | None = None
    errors: list[str] | None = None

    def to_dict(self) -> dict:
        return {
            "discovered": self.discovered,
            "ingested": self.ingested,
            "skipped": self.skipped,
            "by_source": self.by_source or {},
            "errors": self.errors or [],
        }


def _load_env() -> None:
    try:
        from pathlib import Path
        from dotenv import load_dotenv

        api_env = Path(__file__).resolve().parents[1] / ".." / "api" / ".env"
        if api_env.exists():
            load_dotenv(api_env)
    except ImportError:
        pass


def _setup_paths() -> None:
    _load_env()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    api_path = os.path.join(root, "..", "api")
    if api_path not in sys.path:
        sys.path.insert(0, api_path)


def _is_blocked_url(url: str) -> bool:
    return any(url.startswith(p) for p in BLOCKED_SOURCE_URL_PREFIXES)


def _adapter_key(adapter) -> str:
    return getattr(adapter, "report_key", None) or adapter.source_type


def run_all_adapters(
    include_social: bool = False,
    include_search: bool = False,
    auto_discover: bool = True,
) -> CrawlReport:
    _setup_paths()

    from crawler.adapters.web_calendars import WebCalendarAdapter
    from crawler.pipeline import ingest_listings

    adapters = [WebCalendarAdapter()]

    if auto_discover:
        from crawler.adapters.reddit import RedditAdapter
        from crawler.adapters.social_search import SocialSearchAdapter

        adapters.append(SocialSearchAdapter(max_queries=3, max_urls_per_query=5))
        adapters.append(RedditAdapter())
        if not include_search:
            from crawler.adapters.web_search import WebSearchDiscoveryAdapter

            adapters.append(WebSearchDiscoveryAdapter(light=True))

    if include_search:
        from crawler.adapters.public_website import PublicWebsiteAdapter
        from crawler.adapters.web_search import WebSearchDiscoveryAdapter

        adapters.extend(
            [
                WebSearchDiscoveryAdapter(light=False),
                PublicWebsiteAdapter(),
            ]
        )
        if not auto_discover:
            from crawler.adapters.reddit import RedditAdapter

            adapters.append(RedditAdapter())

    if include_social:
        from crawler.adapters.facebook import FacebookAdapter
        from crawler.adapters.instagram import InstagramAdapter

        fb = FacebookAdapter()
        ig = InstagramAdapter()
        if fb.is_configured:
            adapters.append(fb)
        if ig.is_configured:
            adapters.append(ig)

    all_listings = []
    by_source: dict[str, int] = {}
    errors: list[str] = []

    for adapter in adapters:
        try:
            logger.info("Running adapter: %s", type(adapter).__name__)
            found = adapter.discover()
            filtered = [l for l in found if not _is_blocked_url(l.source_url)]
            key = _adapter_key(adapter)
            by_source[key] = by_source.get(key, 0) + len(filtered)
            all_listings.extend(filtered)
            logger.info("Adapter %s found %d listings", key, len(filtered))
            if hasattr(adapter, "last_error") and adapter.last_error:
                errors.append(f"{key}: {adapter.last_error}")
        except Exception as exc:
            key = _adapter_key(adapter)
            msg = f"{key}: {exc}"
            errors.append(msg)
            logger.exception("Adapter failed: %s", type(adapter).__name__)

    logger.info("Ingesting %d listings…", len(all_listings))
    ingested = asyncio.run(ingest_listings(all_listings))
    report = CrawlReport(
        discovered=len(all_listings),
        ingested=ingested,
        skipped=len(all_listings) - ingested,
        by_source=by_source,
        errors=errors,
    )
    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    report = run_all_adapters()
    print(report.to_dict())
