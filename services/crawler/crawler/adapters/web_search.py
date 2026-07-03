"""Discover public loppis pages via DuckDuckGo HTML search (no API key)."""

from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

import httpx

from crawler.adapters.base import RawListing
from crawler.adapters.web_calendars import WebCalendarAdapter
from crawler.discovery.source_registry import SourceRegistry
from crawler.discovery.web_search_client import search_duckduckgo
from crawler.extractors.short_date import parse_short_date_title
from crawler.extractors.swedish_nlp import extract_listing
from crawler.privacy import strip_pii

logger = logging.getLogger(__name__)

from crawler.discovery.sweden import FULL_WEB_SEARCH_QUERIES, LIGHT_WEB_SEARCH_QUERIES

BLOCKED_DOMAINS = {
    "reddit.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "wikipedia.org",
}


class WebSearchDiscoveryAdapter:
    """Use DuckDuckGo HTML results to find public loppis calendar pages, then extract events."""

    source_type = "website"
    report_key = "web_search"

    def __init__(self, max_queries: int | None = None, light: bool = False):
        self.user_agent = "LoppisFinder/1.0 (public web discovery; local-dev)"
        self.last_error: str | None = None
        self._calendar = WebCalendarAdapter()
        self.registry = SourceRegistry()
        self.light = light
        if max_queries is not None:
            self.max_queries = max_queries
        else:
            self.max_queries = len(LIGHT_WEB_SEARCH_QUERIES) if light else len(FULL_WEB_SEARCH_QUERIES)
        self.max_urls_per_query = 5 if light else 8

    def _queries(self) -> list[str]:
        base = LIGHT_WEB_SEARCH_QUERIES if self.light else FULL_WEB_SEARCH_QUERIES
        return base[: self.max_queries]

    def _extract_from_page(self, url: str, html: str) -> list[RawListing]:
        self.registry.extract_calendar_links(url, html)

        if "loppistajm.se" in url:
            base = "https://loppistajm.se"
            return self._calendar._parse_loppistajm_page(html, base, "Stockholm")

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        listings: list[RawListing] = []
        seen: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            text = anchor.get_text(" ", strip=True)
            if not text or len(text) > 180:
                continue
            lower = text.lower()
            if not any(k in lower for k in ("loppis", "loppmarknad", "bakluckeloppis")):
                continue

            start_at, title = parse_short_date_title(text)
            extracted = extract_listing(title or text, text, url, self.source_type)
            if not start_at:
                start_at = extracted.start_at

            link = anchor["href"]
            source_url = link if link.startswith("http") else url
            if source_url in seen:
                continue
            seen.add(source_url)

            listings.append(
                RawListing(
                    title=strip_pii(title or extracted.title) or extracted.title,
                    description=strip_pii(extracted.description),
                    start_at=start_at,
                    address_text=extracted.address_text,
                    municipality=extracted.municipality,
                    lat=None,
                    lng=None,
                    source_url=source_url,
                    source_type=self.source_type,
                    raw_snippet=strip_pii(text[:300]),
                )
            )

        if len(listings) >= 3:
            self.registry.add_calendar_site(url)

        return listings[:30]

    def discover(self) -> list[RawListing]:
        discovered_urls: set[str] = set()
        all_listings: list[RawListing] = []
        seen_listing_urls: set[str] = set()

        for query in self._queries():
            for url in search_duckduckgo(
                query, max_results=self.max_urls_per_query, pause_seconds=1.2 if self.light else 1.5
            ):
                domain = urlparse(url).netloc.lower().replace("www.", "")
                if any(blocked in domain for blocked in BLOCKED_DOMAINS):
                    continue
                if not domain.endswith(".se") and "loppis" not in domain:
                    continue
                if url in discovered_urls:
                    continue
                discovered_urls.add(url)

                try:
                    resp = httpx.get(
                        url,
                        headers={"User-Agent": self.user_agent},
                        timeout=20 if self.light else 25,
                        follow_redirects=True,
                    )
                    if resp.status_code != 200:
                        continue
                    for listing in self._extract_from_page(url, resp.text):
                        if listing.source_url not in seen_listing_urls:
                            seen_listing_urls.add(listing.source_url)
                            all_listings.append(listing)
                    time.sleep(0.8 if self.light else 1.0)
                except httpx.HTTPError:
                    continue

        logger.info(
            "Web search discovery (%s): %d URLs, %d listings",
            "light" if self.light else "full",
            len(discovered_urls),
            len(all_listings),
        )
        return all_listings

    def fetch_detail(self, url: str) -> RawListing | None:
        return None
