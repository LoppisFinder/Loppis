"""Persist crawled listings to database."""

import asyncio
import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from geoalchemy2 import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from crawler.adapters.base import RawListing
from crawler.privacy import strip_pii

from crawler.discovery.sweden import MUNICIPALITY_COORDS, coords_for_municipality

_geocode_cache: dict[str, tuple[float, float]] = {}


async def geocode(address: str | None, municipality: str | None) -> tuple[float, float] | None:
    if municipality:
        for key, coords in MUNICIPALITY_COORDS.items():
            if key.lower() in municipality.lower() or municipality.lower() in key.lower():
                return coords

    query = address or municipality
    if not query:
        return None

    cache_key = query.lower().strip()
    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": f"{query}, Sweden", "format": "json", "limit": 1},
                headers={"User-Agent": "LoppisFinder/1.0 (loppis discovery; local dev)"},
                timeout=15,
            )
            if resp.status_code == 200 and resp.json():
                item = resp.json()[0]
                coords = (float(item["lat"]), float(item["lon"]))
                _geocode_cache[cache_key] = coords
                await asyncio.sleep(1.1)  # Nominatim usage policy
                return coords
    except httpx.HTTPError:
        pass
    return None


async def ingest_listings(listings: list[RawListing]) -> int:
    from app.db_url import normalize_async_database_url
    from app.models import Loppis, LoppisSource, LoppisStatus, SourceType

    raw_url = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://loppis:loppis@localhost:5432/loppisfinder"
    )
    db_url, connect_args = normalize_async_database_url(raw_url)
    engine = create_async_engine(db_url, connect_args=connect_args)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    ingested = 0
    now = datetime.now(timezone.utc)
    pending_scores: list = []

    async with session_factory() as db:
        for listing in listings:
            if not listing.start_at:
                listing.start_at = now + timedelta(days=7)

            coords = None
            if listing.lat and listing.lng:
                coords = (listing.lat, listing.lng)
            elif listing.municipality:
                coords = coords_for_municipality(listing.municipality)
            if not coords:
                coords = await geocode(listing.address_text, listing.municipality)
            if not coords:
                continue

            lat, lng = coords

            existing_source = await db.execute(
                select(LoppisSource).where(LoppisSource.source_url == listing.source_url)
            )
            if existing_source.scalar_one_or_none():
                continue

            try:
                source_type = SourceType(listing.source_type)
            except ValueError:
                source_type = SourceType.website

            loppis = Loppis(
                id=uuid.uuid4(),
                title=strip_pii(listing.title) or listing.title,
                description=strip_pii(listing.description),
                start_at=listing.start_at,
                location=WKTElement(f"POINT({lng} {lat})", srid=4326),
                address_text=strip_pii(listing.address_text),
                municipality=listing.municipality,
                status=LoppisStatus.unverified,
                last_confirmed_at=now,
                tags=["loppis", listing.source_type],
            )
            db.add(loppis)
            await db.flush()

            db.add(
                LoppisSource(
                    loppis_id=loppis.id,
                    source_type=source_type,
                    source_url=listing.source_url,
                    raw_snippet=strip_pii(listing.raw_snippet),
                    source_weight=60,
                )
            )
            pending_scores.append(loppis.id)
            ingested += 1

            if ingested % 25 == 0:
                await db.commit()

        await db.commit()

        # Score in one pass after commit (much faster than per-row during ingest)
        from app.services.loppis_service import recompute_loppis_score

        for loppis_id in pending_scores:
            await recompute_loppis_score(db, loppis_id)
        await db.commit()

    await engine.dispose()
    return ingested
