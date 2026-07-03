"""Shared DuckDuckGo HTML search helper."""

from __future__ import annotations

import time
from urllib.parse import parse_qs, unquote, urlparse

import httpx
from bs4 import BeautifulSoup

USER_AGENT = "LoppisFinder/1.0 (public loppis discovery; local-dev)"


def search_duckduckgo(query: str, max_results: int = 10, pause_seconds: float = 1.0) -> list[str]:
    urls: list[str] = []
    try:
        resp = httpx.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query, "kl": "se-sv"},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
            follow_redirects=True,
        )
        if resp.status_code != 200:
            return urls

        soup = BeautifulSoup(resp.text, "html.parser")
        for link in soup.select("a.result__a"):
            href = link.get("href", "")
            if "uddg=" in href:
                parsed = urlparse(href)
                qs = parse_qs(parsed.query)
                if "uddg" in qs:
                    href = unquote(qs["uddg"][0])
            if href.startswith("http") and href not in urls:
                urls.append(href)
            if len(urls) >= max_results:
                break
        if pause_seconds:
            time.sleep(pause_seconds)
    except httpx.HTTPError:
        pass
    return urls
