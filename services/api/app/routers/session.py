from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import create_access_token, get_current_user
from app.database import get_db
from app.models import AnonymousUser, PushDevice, UserAlert, UserFavorite
from app.privacy import hash_push_token, utcnow
from app.schemas import (
    AlertIn,
    AlertOut,
    AnonymousSessionOut,
    FavoriteIn,
    FavoriteOut,
    PushRegisterIn,
)
from app.services.loppis_service import loppis_to_summary

router = APIRouter(prefix="/v1", tags=["session"])


@router.post("/session/anonymous", response_model=AnonymousSessionOut)
async def create_anonymous_session(db: AsyncSession = Depends(get_db)):
    user = AnonymousUser()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token, expires = create_access_token(user.id)
    return AnonymousSessionOut(
        anonymous_user_id=user.id,
        access_token=token,
        expires_at=expires,
    )


@router.get("/me/export")
async def export_my_data(
    user: AnonymousUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fav_result = await db.execute(
        select(UserFavorite).where(UserFavorite.anonymous_user_id == user.id)
    )
    alert_result = await db.execute(select(UserAlert).where(UserAlert.anonymous_user_id == user.id))
    return {
        "anonymous_user_id": str(user.id),
        "created_at": user.created_at.isoformat(),
        "preferences": user.preferences_json,
        "favorites": [{"loppis_id": str(f.loppis_id), "created_at": f.created_at.isoformat()} for f in fav_result.scalars()],
        "alerts": [
            {
                "id": str(a.id),
                "loppis_id": str(a.loppis_id) if a.loppis_id else None,
                "before_hours": a.before_hours,
            }
            for a in alert_result.scalars()
        ],
    }


@router.delete("/me", status_code=204)
async def delete_my_data(
    user: AnonymousUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(delete(UserFavorite).where(UserFavorite.anonymous_user_id == user.id))
    await db.execute(delete(UserAlert).where(UserAlert.anonymous_user_id == user.id))
    await db.execute(delete(PushDevice).where(PushDevice.anonymous_user_id == user.id))
    await db.delete(user)
    await db.commit()


@router.get("/favorites", response_model=list[FavoriteOut])
async def list_favorites(
    user: AnonymousUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserFavorite)
        .options(selectinload(UserFavorite.loppis))
        .where(UserFavorite.anonymous_user_id == user.id)
        .order_by(UserFavorite.created_at.desc())
    )
    favorites = []
    for fav in result.scalars():
        loppis_summary = None
        if fav.loppis:
            loppis_summary = await loppis_to_summary(db, fav.loppis)
        favorites.append(
            FavoriteOut(
                id=fav.id,
                loppis_id=fav.loppis_id,
                created_at=fav.created_at,
                loppis=loppis_summary,
            )
        )
    return favorites


@router.post("/favorites", response_model=FavoriteOut, status_code=201)
async def add_favorite(
    body: FavoriteIn,
    user: AnonymousUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(UserFavorite).where(
            UserFavorite.anonymous_user_id == user.id,
            UserFavorite.loppis_id == body.loppis_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Redan sparad som favorit")

    fav = UserFavorite(anonymous_user_id=user.id, loppis_id=body.loppis_id)
    db.add(fav)
    await db.commit()
    await db.refresh(fav)
    return FavoriteOut(id=fav.id, loppis_id=fav.loppis_id, created_at=fav.created_at)


@router.delete("/favorites/{favorite_id}", status_code=204)
async def remove_favorite(
    favorite_id: UUID,
    user: AnonymousUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserFavorite).where(
            UserFavorite.id == favorite_id,
            UserFavorite.anonymous_user_id == user.id,
        )
    )
    fav = result.scalar_one_or_none()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorit hittades inte")
    await db.delete(fav)
    await db.commit()


@router.get("/alerts", response_model=list[AlertOut])
async def list_alerts(
    user: AnonymousUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserAlert).where(UserAlert.anonymous_user_id == user.id).order_by(UserAlert.created_at.desc())
    )
    return result.scalars().all()


@router.post("/alerts", response_model=AlertOut, status_code=201)
async def create_alert(
    body: AlertIn,
    user: AnonymousUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alert = UserAlert(
        anonymous_user_id=user.id,
        loppis_id=body.loppis_id,
        radius_km=body.radius_km,
        before_hours=body.before_hours,
        min_score=body.min_score,
        lat=body.lat,
        lng=body.lng,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/alerts/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: UUID,
    user: AnonymousUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserAlert).where(UserAlert.id == alert_id, UserAlert.anonymous_user_id == user.id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Påminnelse hittades inte")
    await db.delete(alert)
    await db.commit()


@router.post("/push/register", status_code=204)
async def register_push(
    body: PushRegisterIn,
    user: AnonymousUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    token_hash = hash_push_token(body.push_token)
    existing = await db.execute(select(PushDevice).where(PushDevice.token_hash == token_hash))
    device = existing.scalar_one_or_none()
    if device:
        device.anonymous_user_id = user.id
        device.platform = body.platform
    else:
        db.add(PushDevice(anonymous_user_id=user.id, token_hash=token_hash, platform=body.platform))
    await db.commit()
