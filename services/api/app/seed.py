"""Seed sample loppis data for development."""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import async_session
from app.models import Loppis, LoppisHistory, LoppisSource, LoppisStatus, SourceType
from app.services.loppis_service import make_point, recompute_loppis_score


SAMPLES = [
    {
        "title": "Stor loppis i Vasastan",
        "description": "Kläder, böcker och leksaker. Kontant och Swish.",
        "lat": 59.342,
        "lng": 18.048,
        "address_text": "Odengatan 12, Stockholm",
        "municipality": "Stockholm",
        "county": "Stockholms län",
        "days_ahead": 7,
        "source_type": SourceType.website,
        "source_url": "https://example.com/loppis/vasastan",
    },
    {
        "title": "Garageloppis i Göteborg",
        "description": "Verktyg, möbler och prylar.",
        "lat": 57.7089,
        "lng": 11.9746,
        "address_text": "Avenyn 45, Göteborg",
        "municipality": "Göteborg",
        "county": "Västra Götalands län",
        "days_ahead": 14,
        "source_type": SourceType.reddit,
        "source_url": "https://reddit.com/r/sweden/comments/example",
    },
    {
        "title": "Sommarloppis i Malmö",
        "description": "Hela familjen rensar — kom tidigt!",
        "lat": 55.605,
        "lng": 13.0038,
        "address_text": "Möllevångstorget, Malmö",
        "municipality": "Malmö",
        "county": "Skåne län",
        "days_ahead": 21,
        "source_type": SourceType.facebook,
        "source_url": "https://facebook.com/events/example",
        "is_recurring": True,
    },
    {
        "title": "Loppis i Uppsala centrum",
        "description": "Vintage och retro.",
        "lat": 59.8586,
        "lng": 17.6389,
        "address_text": "Svartbäcksgatan 8, Uppsala",
        "municipality": "Uppsala",
        "county": "Uppsala län",
        "days_ahead": 3,
        "source_type": SourceType.instagram,
        "source_url": "https://instagram.com/p/example",
    },
    {
        "title": "Neighborhood loppis Linköping",
        "description": "Barnkläder och spel.",
        "lat": 58.4108,
        "lng": 15.6214,
        "address_text": "Storgatan 22, Linköping",
        "municipality": "Linköping",
        "county": "Östergötlands län",
        "days_ahead": 10,
        "source_type": SourceType.forum,
        "source_url": "https://forum.example.com/thread/123",
    },
]


async def seed() -> None:
    async with async_session() as db:
        existing = await db.scalar(select(Loppis.id).limit(1))
        if existing:
            print("Database already seeded, skipping.")
            return

        now = datetime.now(timezone.utc)
        for sample in SAMPLES:
            start = now + timedelta(days=sample["days_ahead"])
            loppis = Loppis(
                id=uuid.uuid4(),
                title=sample["title"],
                description=sample["description"],
                start_at=start,
                end_at=start + timedelta(hours=8),
                is_recurring=sample.get("is_recurring", False),
                location=make_point(sample["lng"], sample["lat"]),
                address_text=sample["address_text"],
                municipality=sample["municipality"],
                county=sample["county"],
                status=LoppisStatus.upcoming,
                last_confirmed_at=now,
                tags=["loppis"],
            )
            db.add(loppis)
            await db.flush()

            db.add(
                LoppisSource(
                    loppis_id=loppis.id,
                    source_type=sample["source_type"],
                    source_url=sample["source_url"],
                    raw_snippet=sample["description"],
                    source_weight=60,
                )
            )

            if sample.get("is_recurring"):
                db.add(
                    LoppisHistory(
                        loppis_id=loppis.id,
                        occurred_at=now - timedelta(days=365),
                        was_accurate=True,
                        photo_urls=[],
                        attendance_signal="mycket folk",
                    )
                )

            await recompute_loppis_score(db, loppis.id)

        await db.commit()
        print(f"Seeded {len(SAMPLES)} loppis listings.")


if __name__ == "__main__":
    asyncio.run(seed())
