"""Public Swedish loppis calendar sites and configurable RSS/HTML sources."""

import json
import os
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from crawler.adapters.base import RawListing
from crawler.extractors.swedish_nlp import extract_listing
from crawler.privacy import strip_pii

DEFAULT_SOURCES = [
    {
        "name": "blocket-loppis",
        "url": "https://www.blocket.se/annonser/hela_sverige/ovrigt/retro_antik?cg=6060&q=loppis",
        "type": "html",
        "link_selector": "a[href*='/annons/']",
        "container": "article, li, div",
    },
]

LOPPIS_KEYWORDS = ["loppis", "loppmarknad", "bakluckeloppis", "garagesale"]


class PublicWebsiteAdapter:
    source_type = "website"

    def __init__(self):
        raw = os.getenv("CRAWL_WEB_SOURCES_JSON", "")
        if raw.strip():
            try:
                self.sources = json.loads(raw)
            except json.JSONDecodeError:
                self.sources = DEFAULT_SOURCES
        else:
            self.sources = DEFAULT_SOURCES

    def _fetch(self, url: str) -> str | None:
        try:
            resp = httpx.get(
                url,
                headers={"User-Agent": "LoppisFinder/1.0 (loppis discovery; local dev)"},
                timeout=30,
                follow_redirects=True,
            )
            if resp.status_code == 200:
                return resp.text
        except httpx.HTTPError:
            pass
        return None

    def _parse_html_source(self, source: dict) -> list[RawListing]:
        html = self._fetch(source["url"])
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        listings: list[RawListing] = []
        seen: set[str] = set()

        for link in soup.select(source.get("link_selector", "a"))[:40]:
            href = link.get("href")
            if not href:
                continue
            url = urljoin(source["url"], href)
            if url in seen:
                continue

            text = link.get_text(" ", strip=True)
            parent = link.find_parent(source.get("container", "div"))
            body = parent.get_text(" ", strip=True)[:500] if parent else text
            combined = f"{text} {body}".lower()

            if not any(kw in combined for kw in LOPPIS_KEYWORDS):
                continue

            seen.add(url)
            extracted = extract_listing(text or "Loppis", body, url, self.source_type)
            listings.append(
                RawListing(
                    title=extracted.title,
                    description=strip_pii(extracted.description),
                    start_at=extracted.start_at,
                    address_text=extracted.address_text,
                    municipality=extracted.municipality,
                    lat=None,
                    lng=None,
                    source_url=url,
                    source_type=self.source_type,
                    raw_snippet=strip_pii(extracted.raw_snippet),
                )
            )
        return listings

    def discover(self) -> list[RawListing]:
        all_listings: list[RawListing] = []
        for source in self.sources:
            if source.get("type", "html") == "html":
                all_listings.extend(self._parse_html_source(source))
        return all_listings

    def fetch_detail(self, url: str) -> RawListing | None:
        return None
