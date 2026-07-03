"""Reddit adapter — OAuth JSON API when configured, RSS fallback otherwise."""

from __future__ import annotations

import logging
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

from crawler.adapters.base import RawListing
from crawler.extractors.swedish_nlp import extract_listing
from crawler.privacy import strip_pii

logger = logging.getLogger(__name__)

SUBREDDITS = ["sweden", "stockholm", "gothenburg", "malmo", "uppsala", "lund"]
LOPPIS_KEYWORDS = ["loppis", "loppmarknad", "bakluckeloppis", "garage sale", "loppisar"]
SEARCH_QUERY = "loppis OR loppmarknad OR bakluckeloppis"


class RedditAdapter:
    source_type = "reddit"
    report_key = "reddit"

    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET", "").strip()
        self.user_agent = os.getenv(
            "REDDIT_USER_AGENT",
            "LoppisFinder/1.0 (Swedish loppis aggregator; contact: local-dev)",
        )
        self.last_error: str | None = None

    @property
    def has_oauth(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def _headers(self, token: str | None = None) -> dict[str, str]:
        h = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def _get_token(self) -> str | None:
        if not self.has_oauth:
            return None
        try:
            resp = httpx.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                headers={"User-Agent": self.user_agent},
                timeout=30,
            )
            if resp.status_code != 200:
                self.last_error = f"Reddit OAuth failed ({resp.status_code}). Check REDDIT_CLIENT_ID/SECRET."
                logger.warning(self.last_error)
                return None
            return resp.json().get("access_token")
        except httpx.HTTPError as exc:
            self.last_error = f"Reddit OAuth error: {exc}"
            return None

    def _fetch_json(self, path: str, params: dict | None, token: str) -> dict | None:
        try:
            resp = httpx.get(
                f"https://oauth.reddit.com{path}",
                params=params,
                headers=self._headers(token),
                timeout=30,
            )
            if resp.status_code == 403:
                self.last_error = "Reddit OAuth returned 403 — verify app type is 'script' and credentials are correct."
                return None
            if resp.status_code != 200:
                return None
            return resp.json()
        except httpx.HTTPError:
            return None

    def _fetch_rss(self, subreddit: str) -> str | None:
        url = f"https://www.reddit.com/r/{subreddit}/search.rss"
        params = {"q": SEARCH_QUERY, "restrict_sr": "1", "sort": "new", "t": "year"}
        try:
            resp = httpx.get(
                url,
                params=params,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "application/rss+xml, application/atom+xml, text/xml",
                },
                timeout=30,
                follow_redirects=True,
            )
            if resp.status_code == 403:
                self.last_error = (
                    "Reddit RSS blocked (403). Add REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to services/api/.env"
                )
                return None
            if resp.status_code != 200:
                return None
            return resp.text
        except httpx.HTTPError:
            return None

    @staticmethod
    def _strip_html(text: str) -> str:
        return re.sub(r"<[^>]+>", " ", text or "").strip()

    def _rss_to_listing(self, title: str, link: str, body: str, pub_date: str | None) -> RawListing | None:
        combined = f"{title} {body}".lower()
        if not any(kw in combined for kw in LOPPIS_KEYWORDS):
            return None

        extracted = extract_listing(title, body, link, self.source_type)
        start_at = extracted.start_at
        if not start_at and pub_date:
            try:
                start_at = parsedate_to_datetime(pub_date)
                if start_at.tzinfo is None:
                    start_at = start_at.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                pass

        return RawListing(
            title=extracted.title,
            description=strip_pii(extracted.description),
            start_at=start_at,
            address_text=extracted.address_text,
            municipality=extracted.municipality,
            lat=None,
            lng=None,
            source_url=link,
            source_type=self.source_type,
            raw_snippet=strip_pii(extracted.raw_snippet or body[:500]),
        )

    def _parse_rss(self, xml_text: str) -> list[RawListing]:
        listings: list[RawListing] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return listings

        for item in root.findall(".//item"):
            title_el = item.find("title")
            link_el = item.find("link")
            if title_el is None or link_el is None or not link_el.text:
                continue
            title = title_el.text or ""
            link = link_el.text.strip()
            desc_el = item.find("description")
            body = self._strip_html(desc_el.text if desc_el is not None else "")
            pub_el = item.find("pubDate")
            pub = pub_el.text if pub_el is not None else None
            listing = self._rss_to_listing(title, link, body, pub)
            if listing:
                listings.append(listing)
        return listings

    def _post_to_listing(self, pd: dict) -> RawListing | None:
        title = pd.get("title", "")
        body = pd.get("selftext", "") or ""
        combined = f"{title} {body}".lower()
        if not any(kw in combined for kw in LOPPIS_KEYWORDS):
            return None

        permalink = pd.get("permalink", "")
        url = f"https://reddit.com{permalink}" if permalink else pd.get("url", "")
        if not url or "reddit.com" not in url:
            return None

        extracted = extract_listing(title, body, url, self.source_type)
        created = pd.get("created_utc")
        start_at = extracted.start_at
        if not start_at and created:
            start_at = datetime.fromtimestamp(created, tz=timezone.utc)

        return RawListing(
            title=extracted.title,
            description=strip_pii(extracted.description),
            start_at=start_at,
            address_text=extracted.address_text,
            municipality=extracted.municipality,
            lat=None,
            lng=None,
            source_url=url,
            source_type=self.source_type,
            raw_snippet=strip_pii(extracted.raw_snippet or body[:500]),
            external_author_id=pd.get("author"),
        )

    def _discover_oauth(self, token: str) -> list[RawListing]:
        seen: set[str] = set()
        listings: list[RawListing] = []

        for sub in SUBREDDITS:
            data = self._fetch_json(
                f"/r/{sub}/search",
                {"q": SEARCH_QUERY, "restrict_sr": "on", "sort": "new", "limit": 50, "t": "year"},
                token,
            )
            if not data:
                continue
            for post in data.get("data", {}).get("children", []):
                listing = self._post_to_listing(post.get("data", {}))
                if listing and listing.source_url not in seen:
                    seen.add(listing.source_url)
                    listings.append(listing)

        global_data = self._fetch_json(
            "/search",
            {"q": f"({SEARCH_QUERY}) AND sweden", "sort": "new", "limit": 50, "t": "year"},
            token,
        )
        if global_data:
            for post in global_data.get("data", {}).get("children", []):
                listing = self._post_to_listing(post.get("data", {}))
                if listing and listing.source_url not in seen:
                    seen.add(listing.source_url)
                    listings.append(listing)

        return listings

    def _discover_rss(self) -> list[RawListing]:
        seen: set[str] = set()
        listings: list[RawListing] = []
        for sub in SUBREDDITS:
            xml_text = self._fetch_rss(sub)
            if not xml_text:
                continue
            for listing in self._parse_rss(xml_text):
                if listing.source_url not in seen:
                    seen.add(listing.source_url)
                    listings.append(listing)
        return listings

    def discover(self) -> list[RawListing]:
        if self.has_oauth:
            token = self._get_token()
            if token:
                results = self._discover_oauth(token)
                if results:
                    logger.info("Reddit OAuth: found %d posts", len(results))
                    return results
                logger.info("Reddit OAuth returned no results, trying RSS fallback")

        if not self.has_oauth:
            logger.info(
                "Reddit JSON API requires OAuth. Using RSS feeds. "
                "For best results set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in services/api/.env"
            )

        results = self._discover_rss()
        if not results and self.last_error:
            logger.warning(self.last_error)
        return results

    def fetch_detail(self, url: str) -> RawListing | None:
        return None
