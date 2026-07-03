from datetime import datetime, timezone

from geoalchemy2 import Geometry, WKTElement
from geoalchemy2.functions import ST_X, ST_Y
from sqlalchemy import cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Loppis, LoppisFeedback, LoppisHistory, LoppisSource, LoppisStatus, SourceType
from app.privacy import utcnow
from app.schemas import LoppisDetailOut, LoppisSummaryOut, ScoreBreakdownOut

SOURCE_TRUST = {
    SourceType.website: 80,
    SourceType.reddit: 60,
    SourceType.facebook: 55,
    SourceType.instagram: 50,
    SourceType.forum: 40,
    SourceType.user_submission: 45,
}

NEGATIVE_PHRASES = ["inställt", "inställd", "fanns inget", "ingen loppis", "stängt", "cancelled"]
POSITIVE_PHRASES = ["bra loppis", "mycket folk", "rekommenderar", "hittade grejer"]


def make_point(lng: float, lat: float) -> WKTElement:
    return WKTElement(f"POINT({lng} {lat})", srid=4326)


async def get_loppis_coords(db: AsyncSession, loppis: Loppis) -> tuple[float, float]:
    geom = cast(Loppis.location, Geometry(geometry_type="POINT", srid=4326))
    result = await db.execute(
        select(ST_Y(geom), ST_X(geom)).where(Loppis.id == loppis.id)
    )
    row = result.one()
    return float(row[0]), float(row[1])


def compute_score_breakdown(
    loppis: Loppis,
    sources: list[LoppisSource],
    feedback: list[LoppisFeedback],
    history: list[LoppisHistory],
) -> ScoreBreakdownOut:
    if loppis.status == LoppisStatus.cancelled:
        return ScoreBreakdownOut(
            source_trust=0,
            confirmation_count=0,
            feedback_sentiment=0,
            historical_accuracy=0,
            freshness=0,
            cancellation_penalty=100,
            total=0,
        )

    source_trust = max((SOURCE_TRUST.get(s.source_type, 40) for s in sources), default=30)
    extra_sources = max(0, len({s.source_type for s in sources}) - 1)
    confirmation = min(24, extra_sources * 8)

    sentiment = 50.0
    for fb in feedback:
        text_lower = (fb.text or "").lower()
        if any(p in text_lower for p in NEGATIVE_PHRASES):
            sentiment -= 20
        elif any(p in text_lower for p in POSITIVE_PHRASES):
            sentiment += 10
        sentiment += fb.sentiment * 10
    sentiment = max(0, min(100, sentiment))

    historical = 50.0
    if history:
        accurate = sum(1 for h in history if h.was_accurate)
        historical = (accurate / len(history)) * 100

    freshness = 50.0
    if loppis.last_confirmed_at:
        days = (utcnow() - loppis.last_confirmed_at).days
        freshness = max(0, 100 - days * 10)

    total = (
        0.35 * source_trust
        + 0.25 * confirmation
        + 0.20 * sentiment
        + 0.10 * historical
        + 0.10 * freshness
    )
    total = max(0, min(100, total))

    return ScoreBreakdownOut(
        source_trust=round(source_trust, 1),
        confirmation_count=round(confirmation, 1),
        feedback_sentiment=round(sentiment, 1),
        historical_accuracy=round(historical, 1),
        freshness=round(freshness, 1),
        cancellation_penalty=0,
        total=round(total, 1),
    )


async def loppis_to_summary(db: AsyncSession, loppis: Loppis, source_count: int = 0) -> LoppisSummaryOut:
    lat, lng = await get_loppis_coords(db, loppis)
    return LoppisSummaryOut(
        id=loppis.id,
        title=loppis.title,
        description=loppis.description,
        start_at=loppis.start_at,
        end_at=loppis.end_at,
        lat=lat,
        lng=lng,
        address_text=loppis.address_text,
        municipality=loppis.municipality,
        county=loppis.county,
        reliability_score=loppis.reliability_score,
        status=loppis.status,
        cover_image_url=loppis.cover_image_url,
        tags=loppis.tags or [],
        source_count=source_count,
    )


async def loppis_to_detail(db: AsyncSession, loppis: Loppis) -> LoppisDetailOut:
    summary = await loppis_to_summary(db, loppis, len(loppis.sources))
    breakdown = compute_score_breakdown(loppis, loppis.sources, loppis.feedback, loppis.history)
    return LoppisDetailOut(
        **summary.model_dump(),
        is_recurring=loppis.is_recurring,
        sources=loppis.sources,
        history=loppis.history,
        score_breakdown=breakdown,
    )


async def list_loppis_nearby(
    db: AsyncSession,
    lat: float,
    lng: float,
    radius_km: float,
    from_dt: datetime | None,
    to_dt: datetime | None,
    min_score: float,
) -> list[LoppisSummaryOut]:
    radius_m = radius_km * 1000
    now = utcnow()
    from_dt = from_dt or now
    to_dt = to_dt or (now + __import__("datetime").timedelta(days=90))

    query = (
        select(Loppis, func.count(LoppisSource.id).label("source_count"))
        .outerjoin(LoppisSource, LoppisSource.loppis_id == Loppis.id)
        .where(
            text(
                "ST_DWithin(loppis.location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius_m)"
            ).bindparams(lng=lng, lat=lat, radius_m=radius_m),
            Loppis.start_at >= from_dt,
            Loppis.start_at <= to_dt,
            Loppis.reliability_score >= min_score,
            Loppis.status != LoppisStatus.cancelled,
        )
        .group_by(Loppis.id)
        .order_by(Loppis.start_at)
    )
    result = await db.execute(query)
    rows = result.all()
    summaries = []
    for loppis, source_count in rows:
        summaries.append(await loppis_to_summary(db, loppis, source_count))
    return summaries


async def get_loppis_detail(db: AsyncSession, loppis_id) -> LoppisDetailOut | None:
    result = await db.execute(
        select(Loppis)
        .options(
            selectinload(Loppis.sources),
            selectinload(Loppis.feedback),
            selectinload(Loppis.history),
        )
        .where(Loppis.id == loppis_id)
    )
    loppis = result.scalar_one_or_none()
    if not loppis:
        return None
    return await loppis_to_detail(db, loppis)


async def recompute_loppis_score(db: AsyncSession, loppis_id) -> None:
    result = await db.execute(
        select(Loppis)
        .options(
            selectinload(Loppis.sources),
            selectinload(Loppis.feedback),
            selectinload(Loppis.history),
        )
        .where(Loppis.id == loppis_id)
    )
    loppis = result.scalar_one_or_none()
    if not loppis:
        return
    breakdown = compute_score_breakdown(loppis, loppis.sources, loppis.feedback, loppis.history)
    loppis.reliability_score = breakdown.total
    if breakdown.total < 40 and loppis.status == LoppisStatus.upcoming:
        loppis.status = LoppisStatus.unverified
    elif breakdown.total >= 40 and loppis.status == LoppisStatus.unverified:
        loppis.status = LoppisStatus.upcoming
