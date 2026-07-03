import scrapy

from crawler.adapters.public_website import PublicWebsiteAdapter
from crawler.adapters.reddit import RedditAdapter


class LoppisSpider(scrapy.Spider):
    name = "loppis"
    allowed_domains: list[str] = []

    def start_requests(self):
        yield scrapy.Request(url="data:,start", callback=self.parse_adapters, dont_filter=True)

    def parse_adapters(self, response):
        adapters = [RedditAdapter(), PublicWebsiteAdapter()]
        for adapter in adapters:
            for listing in adapter.discover():
                yield {
                    "title": listing.title,
                    "source_url": listing.source_url,
                    "source_type": listing.source_type,
                    "start_at": listing.start_at.isoformat() if listing.start_at else None,
                    "address_text": listing.address_text,
                }
