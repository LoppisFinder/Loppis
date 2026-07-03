"""Instagram hashtag adapter via Playwright."""

import os

from crawler.adapters.base import RawListing

HASHTAGS = os.getenv("INSTAGRAM_HASHTAGS", "loppis,loppis2026,loppmarknad").split(",")


class InstagramAdapter:
    source_type = "instagram"

    def __init__(self):
        self.hashtags = [h.strip().lstrip("#") for h in HASHTAGS if h.strip()]
        self.proxy = os.getenv("CRAWLER_PROXY")

    @property
    def is_configured(self) -> bool:
        return os.getenv("INSTAGRAM_CRAWL_ENABLED", "").lower() in ("1", "true", "yes")

    def discover(self) -> list[RawListing]:
        if not self.is_configured:
            return []

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return []

        from crawler.adapters.instagram_playwright import crawl_instagram_hashtags

        return crawl_instagram_hashtags(self.hashtags[:3], self.proxy)

    def fetch_detail(self, url: str) -> RawListing | None:
        return None
