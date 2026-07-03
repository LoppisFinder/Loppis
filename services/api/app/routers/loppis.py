from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from icalendar import Calendar, Event
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import create_access_token, get_current_user
from app.database import get_db
from app.models import AnonymousUser, Loppis, LoppisFeedback, LoppisStatus, ReportType, UserFavorite
from app.privacy import strip_pii, utcnow
from app.schemas import (
    AnonymousSessionOut,
    FavoriteIn,
    FavoriteOut,
    LoppisDetailOut,
    LoppisSubmitIn,
    LoppisSummaryOut,
    ReportIn,
)
from app.services.loppis_service import (
    get_loppis_detail,
    list_loppis_nearby,
    loppis_to_summary,
    make_point,
    recompute_loppis_score,
)
from app.models import LoppisSource, SourceType

router = APIRouter(prefix="/v1/loppis", tags=["loppis"])


@router.get("", response_model=list[LoppisSummaryOut])
async def list_loppis(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(25, ge=1, le=200),
    from_dt: datetime | None = Query(None, alias="from"),
    to_dt: datetime | None = Query(None, alias="to"),
    min_score: float = Query(0, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await list_loppis_nearby(db, lat, lng, radius_km, from_dt, to_dt, min_score)


@router.get("/{loppis_id}", response_model=LoppisDetailOut)
async def get_loppis(loppis_id: UUID, db: AsyncSession = Depends(get_db)):
    detail = await get_loppis_detail(db, loppis_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Loppis hittades inte")
    return detail


@router.get("/{loppis_id}/ics")
async def download_ics(loppis_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Loppis).where(Loppis.id == loppis_id))
    loppis = result.scalar_one_or_none()
    if not loppis:
        raise HTTPException(status_code=404, detail="Loppis hittades inte")

    cal = Calendar()
    cal.add("prodid", "-//LoppisFinder//SE//")
    cal.add("version", "2.0")
    event = Event()
    event.add("summary", loppis.title)
    if loppis.description:
        event.add("description", loppis.description)
    event.add("dtstart", loppis.start_at)
    if loppis.end_at:
        event.add("dtend", loppis.end_at)
    else:
        event.add("dtend", loppis.start_at + timedelta(hours=6))
    if loppis.address_text:
        event.add("location", loppis.address_text)
    event.add("uid", f"loppis-{loppis.id}@loppisfinder.se")
    cal.add_component(event)

    return Response(
        content=cal.to_ical(),
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="loppis-{loppis_id}.ics"'},
    )


@router.post("/{loppis_id}/report", status_code=204)
async def report_loppis(
    loppis_id: UUID,
    body: ReportIn,
    user: AnonymousUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Loppis).where(Loppis.id == loppis_id))
    loppis = result.scalar_one_or_none()
    if not loppis:
        raise HTTPException(status_code=404, detail="Loppis hittades inte")

    sentiment = -0.5 if body.report_type == ReportType.cancelled else -0.2
    feedback = LoppisFeedback(
        loppis_id=loppis_id,
        sentiment=sentiment,
        text=strip_pii(body.text),
        reporter_anonymous_id=user.id,
        report_type=body.report_type,
    )
    db.add(feedback)
    await db.flush()

    if body.report_type == ReportType.cancelled:
        cancel_count = await db.scalar(
            select(func.count())
            .select_from(LoppisFeedback)
            .where(
                LoppisFeedback.loppis_id == loppis_id,
                LoppisFeedback.report_type == ReportType.cancelled,
            )
        )
        if cancel_count and cancel_count >= 3:
            loppis.status = LoppisStatus.cancelled
            loppis.reliability_score = 0

    await recompute_loppis_score(db, loppis_id)
    await db.commit()


@router.post("/submit", response_model=LoppisDetailOut, status_code=201)
async def submit_loppis(
    body: LoppisSubmitIn,
    user: AnonymousUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    loppis = Loppis(
        title=strip_pii(body.title) or body.title,
        description=strip_pii(body.description),
        start_at=body.start_at,
        end_at=body.end_at,
        location=make_point(body.lng, body.lat),
        address_text=strip_pii(body.address_text),
        reliability_score=45,
        status=LoppisStatus.unverified,
    )
    db.add(loppis)
    await db.flush()

    source = LoppisSource(
        loppis_id=loppis.id,
        source_type=SourceType.user_submission,
        source_url=body.source_url or f"user://{user.id}",
        raw_snippet=strip_pii(body.description),
        source_weight=45,
    )
    db.add(source)
    await db.commit()

    detail = await get_loppis_detail(db, loppis.id)
    return detail
