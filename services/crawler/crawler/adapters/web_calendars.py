"""Crawl public loppis calendar websites (curated Swedish sources)."""

from __future__ import annotations

import json
import logging
import os
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from crawler.adapters.base import RawListing
from crawler.extractors.short_date import parse_short_date_title
from crawler.privacy import strip_pii

logger = logging.getLogger(__name__)

from crawler.discovery.source_registry import SourceRegistry
from crawler.discovery.sweden import MUNICIPALITY_COORDS as SWEDEN_MUNICIPALITIES
from crawler.discovery.sweden import infer_site_location

USER_AGENT = "LoppisFinder/1.0 (public calendar aggregator; +local-dev)"

# Known venue → (address, municipality, lat, lng)
VENUE_HINTS: dict[str, tuple[str, str, float, float]] = {
    "karlaplan": ("Karlaplan, Stockholm", "Stockholm", 59.3379, 18.0954),
    "mariatorget": ("Mariatorget, Stockholm", "Stockholm", 59.3175, 18.0527),
    "hötorget": ("Hötorget, Stockholm", "Stockholm", 59.3350, 18.0632),
    "hotorget": ("Hötorget, Stockholm", "Stockholm", 59.3350, 18.0632),
    "solvalla": ("Solvalla, Stockholm", "Stockholm", 59.3650, 17.9800),
    "roslagsstoppet": ("Roslagsstoppet, Täby", "Stockholm", 59.4439, 18.0687),
    "hågelby": ("Hågelby gård, Botkyrka", "Stockholm", 59.2390, 17.8120),
    "hagelby": ("Hågelby gård, Botkyrka", "Stockholm", 59.2390, 17.8120),
}

DEFAULT_CALENDAR_SITES = [
    {
        "name": "loppistajm",
        "base_url": "https://loppistajm.se",
        "pages": ["/kalender.html", "/"],
        "link_pattern": r"^\d{1,2}/\d{1,2}\s",
        "municipality_default": "Stockholm",
    },
]


class WebCalendarAdapter:
    """Scrape publicly listed loppis calendars on the open web."""

    source_type = "website"
    report_key = "web_calendar"

    def __init__(self):
        raw = os.getenv("CRAWL_CALENDAR_SITES_JSON", "")
        if raw.strip():
            try:
                base_sites = json.loads(raw)
            except json.JSONDecodeError:
                base_sites = DEFAULT_CALENDAR_SITES
        else:
            base_sites = DEFAULT_CALENDAR_SITES
        self.sites = SourceRegistry().merge_calendar_sites(base_sites)
        self.registry = SourceRegistry()

    def _fetch(self, url: str) -> str | None:
        try:
            resp = httpx.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=30,
                follow_redirects=True,
            )
            if resp.status_code == 200:
                return resp.text
        except httpx.HTTPError as exc:
            logger.warning("Fetch failed %s: %s", url, exc)
        return None

    def _venue_hint(self, text: str) -> tuple[str | None, str | None, float | None, float | None]:
        lower = text.lower()
        for key, (address, municipality, lat, lng) in VENUE_HINTS.items():
            if key in lower:
                return address, municipality, lat, lng
        return None, None, None, None

    def _site_location(self, site: dict) -> tuple[str | None, str | None, float | None, float | None]:
        municipality, lat, lng = infer_site_location(site.get("name", ""), site.get("base_url", ""))
        if municipality:
            return None, municipality, lat, lng
        default = site.get("municipality_default")
        if default:
            coords = SWEDEN_MUNICIPALITIES.get(default)
            if coords:
                return None, default, coords[0], coords[1]
        return None, default, None, None

    def _parse_loppistajm_page(
        self, html: str, base_url: str, default_municipality: str | None
    ) -> list[RawListing]:
        soup = BeautifulSoup(html, "html.parser")
        listings: list[RawListing] = []
        seen: set[tuple[str, str]] = set()

        for anchor in soup.find_all("a", href=True):
            raw_text = anchor.get_text(" ", strip=True)
            if not raw_text or not re.match(r"^\d{1,2}/\d{1,2}\s", raw_text):
                continue

            start_at, title = parse_short_date_title(raw_text, keep_current_year=True)
            if not start_at:
                continue

            href = anchor["href"].strip()
            source_url = urljoin(base_url, href) if not href.startswith("http") else href
            dedup_key = (source_url, start_at.date().isoformat())
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            address, municipality, lat, lng = self._venue_hint(title)
            if not lat:
                _, site_muni, site_lat, site_lng = self._site_location(
                    {"name": base_url, "base_url": base_url, "municipality_default": default_municipality}
                )
                municipality = municipality or site_muni
                lat = lat or site_lat
                lng = lng or site_lng
            municipality = municipality or default_municipality

            listings.append(
                RawListing(
                    title=strip_pii(title) or title,
                    description=strip_pii(f"Loppis enligt {base_url}"),
                    start_at=start_at,
                    address_text=address,
                    municipality=municipality,
                    lat=lat,
                    lng=lng,
                    source_url=source_url,
                    source_type=self.source_type,
                    raw_snippet=strip_pii(raw_text),
                )
            )
        return listings

    def _parse_generic_page(self, html: str, base_url: str, site: dict) -> list[RawListing]:
        soup = BeautifulSoup(html, "html.parser")
        listings: list[RawListing] = []
        seen: set[str] = set()
        pattern = site.get("link_pattern", "loppis")

        for anchor in soup.find_all("a", href=True):
            text = anchor.get_text(" ", strip=True)
            if not text or len(text) > 200:
                continue
            if not re.search(pattern, text, re.IGNORECASE):
                continue
            if "loppis" not in text.lower() and "bakluck" not in text.lower():
                continue

            href = anchor["href"].strip()
            source_url = urljoin(base_url, href) if not href.startswith("http") else href
            if source_url in seen or source_url.rstrip("/") == base_url.rstrip("/"):
                continue
            seen.add(source_url)

            start_at, title = parse_short_date_title(text, keep_current_year=True)
            if not title:
                title = text

            address, municipality, lat, lng = self._venue_hint(title)
            if not lat:
                _, site_muni, site_lat, site_lng = self._site_location(site)
                municipality = municipality or site_muni
                lat = lat or site_lat
                lng = lng or site_lng
            listings.append(
                RawListing(
                    title=strip_pii(title) or title,
                    description=None,
                    start_at=start_at,
                    address_text=address,
                    municipality=municipality or site.get("municipality_default"),
                    lat=lat,
                    lng=lng,
                    source_url=source_url,
                    source_type=self.source_type,
                    raw_snippet=strip_pii(text[:300]),
                )
            )
        return listings

    def discover(self) -> list[RawListing]:
        all_listings: list[RawListing] = []
        seen_urls: set[str] = set()

        for site in self.sites:
            base = site["base_url"].rstrip("/")
            for page in site.get("pages", ["/"]):
                url = urljoin(base + "/", page.lstrip("/"))
                html = self._fetch(url)
                if not html:
                    continue

                self.registry.extract_calendar_links(url, html)

                if site.get("name") == "loppistajm" or "loppistajm.se" in base:
                    found = self._parse_loppistajm_page(html, base, site.get("municipality_default"))
                else:
                    found = self._parse_generic_page(html, base, site)

                for listing in found:
                    unique_key = f"{listing.source_url}#d={listing.start_at.date().isoformat() if listing.start_at else 'unknown'}"
                    listing.source_url = unique_key
                    if unique_key not in seen_urls:
                        seen_urls.add(unique_key)
                        all_listings.append(listing)

                logger.info("Web calendar %s %s → %d listings", site.get("name"), url, len(found))

        return all_listings

    def fetch_detail(self, url: str) -> RawListing | None:
        return None
