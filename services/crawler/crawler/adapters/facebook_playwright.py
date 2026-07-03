"""Playwright implementation for Facebook groups."""

from datetime import datetime, timezone

from crawler.adapters.base import RawListing
from crawler.extractors.swedish_nlp import extract_listing
from crawler.privacy import strip_pii

LOPPIS_KEYWORDS = ["loppis", "garage sale", "loppmarknad"]


def crawl_facebook_groups(group_urls: list[str], proxy: str | None) -> list[RawListing]:
    from playwright.sync_api import sync_playwright

    listings: list[RawListing] = []
    with sync_playwright() as p:
        launch_opts: dict = {"headless": True}
        if proxy:
            launch_opts["proxy"] = {"server": proxy}
        browser = p.chromium.launch(**launch_opts)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()
        for group_url in group_urls:
            try:
                page.goto(group_url, timeout=60000)
                page.wait_for_timeout(3000)
                posts = page.query_selector_all('[role="article"]')
                for post in posts[:15]:
                    text = post.inner_text()
                    if not any(kw in text.lower() for kw in LOPPIS_KEYWORDS):
                        continue
                    lines = text.split("\n")
                    title = lines[0][:200] if lines else "Loppis"
                    extracted = extract_listing(title, text, group_url, "facebook")
                    listings.append(
                        RawListing(
                            title=extracted.title,
                            description=strip_pii(extracted.description),
                            start_at=extracted.start_at or datetime.now(timezone.utc),
                            address_text=extracted.address_text,
                            municipality=extracted.municipality,
                            lat=None,
                            lng=None,
                            source_url=group_url,
                            source_type="facebook",
                            raw_snippet=strip_pii(extracted.raw_snippet),
                        )
                    )
            except Exception:
                continue
        browser.close()
    return listings
