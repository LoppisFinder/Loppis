"""Persist newly discovered calendar sites and social URLs between crawls."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "data" / "discovered_sources.json"

CALENDAR_HINTS = ("kalender", "loppis", "loppmarknad", "event", "marknad")
SOCIAL_BLOCKLIST = {"facebook.com/login", "facebook.com/share", "instagram.com/accounts"}


class SourceRegistry:
    def __init__(self, path: Path | None = None):
        self.path = path or REGISTRY_PATH
        self._data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {"calendar_sites": [], "facebook_groups": [], "last_updated": None}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read source registry: %s", exc)
            return {"calendar_sites": [], "facebook_groups": [], "last_updated": None}

    def save(self) -> None:
        self._data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    def calendar_sites(self) -> list[dict]:
        return list(self._data.get("calendar_sites", []))

    def facebook_groups(self) -> list[str]:
        return list(self._data.get("facebook_groups", []))

    def merge_calendar_sites(self, base_sites: list[dict]) -> list[dict]:
        merged: dict[str, dict] = {}
        for site in base_sites:
            base_url = site.get("base_url", "").rstrip("/")
            if base_url:
                merged[base_url] = site
        for site in self.calendar_sites():
            base_url = site.get("base_url", "").rstrip("/")
            if base_url and base_url not in merged:
                merged[base_url] = site
        return list(merged.values())

    def add_calendar_site(self, url: str, name: str | None = None) -> bool:
        parsed = urlparse(url)
        if not parsed.scheme.startswith("http") or not parsed.netloc:
            return False
        base_url = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
        lower = url.lower()
        if not any(h in lower for h in CALENDAR_HINTS) and "loppis" not in parsed.netloc:
            return False

        existing = {s.get("base_url", "").rstrip("/") for s in self.calendar_sites()}
        if base_url in existing:
            return False

        site = {
            "name": name or parsed.netloc.replace("www.", ""),
            "base_url": base_url,
            "pages": [parsed.path or "/"],
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            "link_pattern": "loppis|loppmarknad|bakluck|\\d{1,2}/\\d{1,2}",
        }
        self._data.setdefault("calendar_sites", []).append(site)
        self.save()
        logger.info("Registered new calendar site: %s", base_url)
        return True

    def add_facebook_group(self, url: str) -> bool:
        if not url.startswith("http") or "/groups/" not in url:
            return False
        if any(blocked in url for blocked in SOCIAL_BLOCKLIST):
            return False
        clean = url.split("?")[0].rstrip("/")
        existing = set(self.facebook_groups())
        if clean in existing:
            return False
        self._data.setdefault("facebook_groups", []).append(clean)
        self.save()
        logger.info("Registered Facebook group: %s", clean)
        return True

    def extract_calendar_links(self, page_url: str, html: str) -> list[str]:
        from bs4 import BeautifulSoup

        found: list[str] = []
        soup = BeautifulSoup(html, "html.parser")
        page_host = urlparse(page_url).netloc.lower().replace("www.", "")

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if not href.startswith("http"):
                continue
            parsed = urlparse(href)
            host = parsed.netloc.lower().replace("www.", "")
            path_lower = parsed.path.lower()
            if host == page_host:
                continue
            if not host.endswith(".se") and "loppis" not in host:
                continue
            if any(h in path_lower or h in href.lower() for h in CALENDAR_HINTS):
                found.append(href.split("#")[0])
                self.add_calendar_site(href)
        return found
