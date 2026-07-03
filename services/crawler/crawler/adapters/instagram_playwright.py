"""Playwright implementation for Instagram hashtags."""

from datetime import datetime, timezone

from crawler.adapters.base import RawListing
from crawler.extractors.swedish_nlp import extract_listing
from crawler.privacy import strip_pii


def crawl_instagram_hashtags(hashtags: list[str], proxy: str | None) -> list[RawListing]:
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
        for tag in hashtags:
            try:
                page.goto(f"https://www.instagram.com/explore/tags/{tag}/", timeout=60000)
                page.wait_for_timeout(4000)
                articles = page.query_selector_all("article")
                for article in articles[:10]:
                    text = article.inner_text()
                    if "loppis" not in text.lower():
                        continue
                    url = f"https://www.instagram.com/explore/tags/{tag}/"
                    extracted = extract_listing(f"Loppis #{tag}", text, url, "instagram")
                    listings.append(
                        RawListing(
                            title=extracted.title,
                            description=strip_pii(extracted.description),
                            start_at=extracted.start_at or datetime.now(timezone.utc),
                            address_text=extracted.address_text,
                            municipality=extracted.municipality,
                            lat=None,
                            lng=None,
                            source_url=url,
                            source_type="instagram",
                            raw_snippet=strip_pii(extracted.raw_snippet),
                        )
                    )
            except Exception:
                continue
        browser.close()
    return listings
