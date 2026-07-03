"""Facebook group posts adapter via Playwright."""

import os

from crawler.adapters.base import RawListing
from crawler.discovery.source_registry import SourceRegistry

LOPPIS_KEYWORDS = ["loppis", "garage sale", "loppmarknad"]


class FacebookAdapter:
    source_type = "facebook"
    report_key = "facebook_playwright"

    def __init__(self):
        env_groups = [u.strip() for u in os.getenv("FACEBOOK_GROUP_URLS", "").split(",") if u.strip()]
        discovered = SourceRegistry().facebook_groups()
        self.group_urls = list(dict.fromkeys(env_groups + discovered))
        self.proxy = os.getenv("CRAWLER_PROXY")

    @property
    def is_configured(self) -> bool:
        return len(self.group_urls) > 0

    def discover(self) -> list[RawListing]:
        if not self.group_urls:
            return []

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return []

        from crawler.adapters.facebook_playwright import crawl_facebook_groups

        return crawl_facebook_groups(self.group_urls, self.proxy)

    def fetch_detail(self, url: str) -> RawListing | None:
        return None
