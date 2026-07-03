# Crawler sources

LoppisFinder **automatically discovers** loppis from public web calendars, search engines, Facebook events, Instagram posts, and Reddit — without manual URL lists.

## What runs automatically

Every crawl (button, API, or scheduled every 6 hours while the API runs):

1. **Known + discovered calendars** — loppistajm.se, loppis.info, plus sites found on previous crawls
2. **Light web search** — DuckDuckGo finds new `.se` loppis calendar pages
3. **Social search** — public Facebook events and Instagram posts via web search + OG metadata
4. **Reddit RSS** — r/sweden, stockholm, gothenburg, etc.

Discovered calendar sites and Facebook groups are saved to `services/crawler/data/discovered_sources.json` and reused on the next crawl.

## Optional deep crawl

```powershell
# Deep search + Blocket (2–5 min)
Invoke-RestMethod -Uri "http://localhost:8000/v1/crawl/run?include_search=true" -Method POST

# Playwright Facebook groups (needs playwright + group URLs or discovered groups)
Invoke-RestMethod -Uri "http://localhost:8000/v1/crawl/run?include_social=true" -Method POST
```

## Environment

```env
# Automatic background crawl while API runs (0 = disabled)
CRAWL_AUTO_INTERVAL_HOURS=6

# Extra curated calendar sites (JSON array)
CRAWL_CALENDAR_SITES_JSON=[{"name":"mysite","base_url":"https://example.se","pages":["/kalender"]}]

# Playwright Facebook groups (optional — groups are also auto-discovered via search)
FACEBOOK_GROUP_URLS=https://www.facebook.com/groups/...

# Reddit OAuth (optional — RSS works without keys)
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
```

## Limits

- **Facebook/Instagram**: public pages only; login-walled content needs `include_social=true` + Playwright + group URLs
- **Rate limits**: DuckDuckGo and Nominatim are throttled to stay polite
- **Legal**: only public data; respect site terms

## Scheduled crawls (production)

With Redis + Celery: `worker.tasks.run_crawlers` (uses full auto-discovery).

Without Redis: set `CRAWL_AUTO_INTERVAL_HOURS=6` in `services/api/.env`.
