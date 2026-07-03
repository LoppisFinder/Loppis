import asyncio
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from worker.celery_app import celery_app

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://loppis:loppis@localhost:5432/loppisfinder"
)


def run_async(coro):
    return asyncio.run(coro)


@celery_app.task(name="worker.tasks.run_crawlers")
def run_crawlers():
    import sys
    import os
    crawler_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "crawler"))
    api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "api"))
    for path in (crawler_root, api_root):
        if path not in sys.path:
            sys.path.insert(0, path)
    from crawler.runner import run_all_adapters
    return run_all_adapters(include_social=False, include_search=False, auto_discover=True).to_dict()


@celery_app.task(name="worker.tasks.recompute_all_scores")
def recompute_all_scores():
    async def _run():
        from app.models import Loppis
        from app.services.loppis_service import recompute_loppis_score

        engine = create_async_engine(DATABASE_URL)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        updated = 0
        async with session_factory() as db:
            result = await db.execute(select(Loppis.id))
            for (loppis_id,) in result.all():
                await recompute_loppis_score(db, loppis_id)
                updated += 1
            await db.commit()
        await engine.dispose()
        return {"updated": updated}

    return run_async(_run())


@celery_app.task(name="worker.tasks.process_alerts")
def process_alerts():
    async def _run():
        from app.models import Loppis, LoppisStatus, PushDevice, UserAlert
        from app.services.loppis_service import list_loppis_nearby

        engine = create_async_engine(DATABASE_URL)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        sent = 0
        now = datetime.now(timezone.utc)

        async with session_factory() as db:
            result = await db.execute(
                select(UserAlert)
                .options(selectinload(UserAlert.user))
                .where(UserAlert.is_active == True)
            )
            alerts = result.scalars().all()

            for alert in alerts:
                if alert.loppis_id:
                    loppis_result = await db.execute(select(Loppis).where(Loppis.id == alert.loppis_id))
                    loppis = loppis_result.scalar_one_or_none()
                    if not loppis or loppis.status == LoppisStatus.cancelled:
                        continue
                    notify_at = loppis.start_at - timedelta(hours=alert.before_hours)
                    if now >= notify_at and now <= loppis.start_at:
                        devices = await db.execute(
                            select(PushDevice).where(PushDevice.anonymous_user_id == alert.anonymous_user_id)
                        )
                        if devices.scalars().first():
                            sent += 1
                elif alert.lat and alert.lng and alert.radius_km:
                    nearby = await list_loppis_nearby(
                        db, alert.lat, alert.lng, alert.radius_km, now, now + timedelta(days=7), alert.min_score
                    )
                    if nearby:
                        sent += 1

        await engine.dispose()
        return {"notifications_queued": sent}

    return run_async(_run())


@celery_app.task(name="worker.tasks.purge_old_data")
def purge_old_data():
    async def _run():
        from app.models import AnonymousUser, Loppis, LoppisStatus

        engine = create_async_engine(DATABASE_URL)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        cutoff_events = datetime.now(timezone.utc) - timedelta(days=90)
        cutoff_users = datetime.now(timezone.utc) - timedelta(days=365)

        async with session_factory() as db:
            await db.execute(
                delete(Loppis).where(
                    Loppis.end_at < cutoff_events,
                    Loppis.status == LoppisStatus.past,
                )
            )
            inactive = await db.execute(
                select(AnonymousUser).where(AnonymousUser.last_seen_at < cutoff_users)
            )
            for user in inactive.scalars():
                await db.delete(user)
            await db.commit()
        await engine.dispose()
        return {"purged": True}

    return run_async(_run())
