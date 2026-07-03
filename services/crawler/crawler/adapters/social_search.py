"""Discover public Facebook events and Instagram posts via web search (no API keys)."""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from crawler.adapters.base import RawListing
from crawler.discovery.source_registry import SourceRegistry
from crawler.discovery.web_search_client import search_duckduckgo
from crawler.extractors.swedish_nlp import extract_listing
from crawler.privacy import strip_pii

logger = logging.getLogger(__name__)

from crawler.discovery.sweden import SOCIAL_SEARCH_QUERIES

LOPPIS_KEYWORDS = ("loppis", "loppmarknad", "bakluckeloppis", "garage sale", "loppisar")


class SocialSearchAdapter:
    """Find public social posts/events by searching the open web, then scrape OG metadata."""

    source_type = "social_discovery"
    report_key = "social_search"

    def __init__(self, max_queries: int = 4, max_urls_per_query: int = 6):
        self.max_queries = max_queries
        self.max_urls_per_query = max_urls_per_query
        self.user_agent = "LoppisFinder/1.0 (social discovery; local-dev)"
        self.last_error: str | None = None
        self.registry = SourceRegistry()

    def _fetch(self, url: str) -> str | None:
        try:
            resp = httpx.get(
                url,
                headers={"User-Agent": self.user_agent, "Accept-Language": "sv-SE,sv;q=0.9"},
                timeout=20,
                follow_redirects=True,
            )
            if resp.status_code == 200:
                return resp.text
        except httpx.HTTPError:
            pass
        return None

    def _meta_tags(self, html: str) -> dict[str, str]:
        soup = BeautifulSoup(html, "html.parser")
        meta: dict[str, str] = {}
        for tag in soup.find_all("meta"):
            key = tag.get("property") or tag.get("name")
            content = tag.get("content")
            if key and content:
                meta[key] = content
        return meta

    def _json_ld_event(self, html: str) -> dict | None:
        soup = BeautifulSoup(html, "html.parser")
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get("@type") in ("Event", "SocialEvent"):
                    return item
        return None

    def _parse_event_page(self, url: str, html: str) -> RawListing | None:
        meta = self._meta_tags(html)
        title = meta.get("og:title") or meta.get("twitter:title") or "Loppis"
        description = meta.get("og:description") or meta.get("description") or ""
        combined = f"{title} {description}".lower()
        if not any(kw in combined for kw in LOPPIS_KEYWORDS):
            return None

        start_at = None
        event = self._json_ld_event(html)
        if event:
            start_raw = event.get("startDate")
            if start_raw:
                try:
                    start_at = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
                except ValueError:
                    pass

        extracted = extract_listing(title, description, url, "facebook")
        if not start_at:
            start_at = extracted.start_at

        location = None
        if event and isinstance(event.get("location"), dict):
            location = event["location"].get("name") or event["location"].get("address")

        return RawListing(
            title=strip_pii(extracted.title) or title[:200],
            description=strip_pii(extracted.description or description),
            start_at=start_at,
            address_text=extracted.address_text or location,
            municipality=extracted.municipality,
            lat=None,
            lng=None,
            source_url=url.split("?")[0],
            source_type="facebook",
            raw_snippet=strip_pii(description[:500]),
        )

    def _parse_instagram_page(self, url: str, html: str) -> RawListing | None:
        meta = self._meta_tags(html)
        title = meta.get("og:title") or "Loppis"
        description = meta.get("og:description") or ""
        combined = f"{title} {description}".lower()
        if not any(kw in combined for kw in LOPPIS_KEYWORDS):
            return None

        extracted = extract_listing(title, description, url, "instagram")
        return RawListing(
            title=strip_pii(extracted.title) or title[:200],
            description=strip_pii(extracted.description),
            start_at=extracted.start_at,
            address_text=extracted.address_text,
            municipality=extracted.municipality,
            lat=None,
            lng=None,
            source_url=url.split("?")[0],
            source_type="instagram",
            raw_snippet=strip_pii(description[:500]),
        )

    def discover(self) -> list[RawListing]:
        listings: list[RawListing] = []
        seen: set[str] = set()

        for query in SOCIAL_SEARCH_QUERIES[: self.max_queries]:
            for url in search_duckduckgo(query, max_results=self.max_urls_per_query, pause_seconds=1.2):
                lower = url.lower()
                if "facebook.com/groups/" in lower:
                    self.registry.add_facebook_group(url)
                    continue

                if "facebook.com/events/" in lower or re.search(r"facebook\.com/events/\d+", lower):
                    clean = url.split("?")[0]
                    if clean in seen:
                        continue
                    html = self._fetch(clean)
                    if not html:
                        continue
                    listing = self._parse_event_page(clean, html)
                    if listing:
                        seen.add(clean)
                        listings.append(listing)
                    time.sleep(0.8)
                    continue

                if "instagram.com/p/" in lower or "instagram.com/reel/" in lower:
                    clean = url.split("?")[0]
                    if clean in seen:
                        continue
                    html = self._fetch(clean)
                    if not html:
                        continue
                    listing = self._parse_instagram_page(clean, html)
                    if listing:
                        seen.add(clean)
                        listings.append(listing)
                    time.sleep(0.8)

        logger.info("Social search discovery: %d listings", len(listings))
        return listings

    def fetch_detail(self, url: str) -> RawListing | None:
        return None
