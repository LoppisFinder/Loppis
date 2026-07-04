import asyncio
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_admin_token, require_admin
from app.config import settings
from app.database import get_db
from app.models import FeedSourceKind
from app.routers.crawl import CrawlReportOut, CrawlStatusOut, get_crawl_status_data, start_crawl_job
from app.services.crawl_admin import (
    create_feed_source,
    delete_feed_source,
    get_crawl_settings,
    list_feed_sources,
    set_feed_source_enabled,
    update_crawl_settings,
)

router = APIRouter(prefix="/v1/admin", tags=["admin"])


class AdminLoginIn(BaseModel):
    password: str


class AdminLoginOut(BaseModel):
    access_token: str
    expires_at: str


class FeedSourceOut(BaseModel):
    id: str
    name: str
    url: str
    kind: str
    pages: list[str] | None
    enabled: bool
    created_at: str


class FeedSourceIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=8, max_length=2000)
    kind: FeedSourceKind = FeedSourceKind.calendar
    pages: list[str] | None = None


class CrawlSettingsOut(BaseModel):
    auto_enabled: bool
    interval_hours: float
    auto_discover: bool
    include_search: bool
    include_social: bool
    data_version: str
    last_run_at: str | None
    last_ingested: int


class CrawlSettingsIn(BaseModel):
    auto_enabled: bool | None = None
    interval_hours: float | None = Field(default=None, ge=0.5, le=168)
    auto_discover: bool | None = None
    include_search: bool | None = None
    include_social: bool | None = None


def _source_out(source) -> FeedSourceOut:
    return FeedSourceOut(
        id=str(source.id),
        name=source.name,
        url=source.url,
        kind=source.kind.value,
        pages=source.pages,
        enabled=source.enabled,
        created_at=source.created_at.isoformat(),
    )


@router.post("/login", response_model=AdminLoginOut)
async def admin_login(body: AdminLoginIn):
    if not settings.admin_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin is not configured (set ADMIN_PASSWORD on the API)",
        )
    if body.password != settings.admin_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    token, expires = create_admin_token()
    return AdminLoginOut(access_token=token, expires_at=expires.isoformat())


@router.get("/sources", response_model=list[FeedSourceOut])
async def admin_list_sources(
    _: Annotated[None, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
):
    sources = await list_feed_sources(db)
    return [_source_out(source) for source in sources]


@router.post("/sources", response_model=FeedSourceOut, status_code=status.HTTP_201_CREATED)
async def admin_create_source(
    body: FeedSourceIn,
    _: Annotated[None, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
):
    source = await create_feed_source(
        db,
        name=body.name,
        url=body.url,
        kind=body.kind,
        pages=body.pages,
    )
    return _source_out(source)


@router.patch("/sources/{source_id}", response_model=FeedSourceOut)
async def admin_toggle_source(
    source_id: uuid.UUID,
    enabled: bool,
    _: Annotated[None, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
):
    source = await set_feed_source_enabled(db, source_id, enabled)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return _source_out(source)


@router.delete("/sources/{source_id}")
async def admin_delete_source(
    source_id: uuid.UUID,
    _: Annotated[None, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
):
    if not await delete_feed_source(db, source_id):
        raise HTTPException(status_code=404, detail="Source not found")
    return {"deleted": True}


@router.get("/crawl/settings", response_model=CrawlSettingsOut)
async def admin_get_crawl_settings(
    _: Annotated[None, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
):
    crawl = await get_crawl_settings(db)
    return CrawlSettingsOut(
        auto_enabled=crawl.auto_enabled,
        interval_hours=crawl.interval_hours,
        auto_discover=crawl.auto_discover,
        include_search=crawl.include_search,
        include_social=crawl.include_social,
        data_version=crawl.data_version,
        last_run_at=crawl.last_run_at.isoformat() if crawl.last_run_at else None,
        last_ingested=crawl.last_ingested,
    )


@router.patch("/crawl/settings", response_model=CrawlSettingsOut)
async def admin_update_crawl_settings(
    body: CrawlSettingsIn,
    _: Annotated[None, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
):
    crawl = await update_crawl_settings(db, **body.model_dump(exclude_unset=True))
    return CrawlSettingsOut(
        auto_enabled=crawl.auto_enabled,
        interval_hours=crawl.interval_hours,
        auto_discover=crawl.auto_discover,
        include_search=crawl.include_search,
        include_social=crawl.include_social,
        data_version=crawl.data_version,
        last_run_at=crawl.last_run_at.isoformat() if crawl.last_run_at else None,
        last_ingested=crawl.last_ingested,
    )


@router.get("/crawl/status", response_model=CrawlStatusOut)
async def admin_crawl_status(_: Annotated[None, Depends(require_admin)]):
    return get_crawl_status_data()


@router.post("/crawl/run", response_model=CrawlReportOut)
async def admin_run_crawl(
    background_tasks: BackgroundTasks,
    _: Annotated[None, Depends(require_admin)],
    sync: bool = False,
):
    from app.routers.crawl import _running, start_crawl_job

    if _running:
        raise HTTPException(status_code=409, detail="Crawl already running")

    if sync:
        return await asyncio.to_thread(start_crawl_job)

    background_tasks.add_task(start_crawl_job)
    return CrawlReportOut(
        discovered=0,
        ingested=0,
        skipped=0,
        by_source={},
        errors=["Crawl started in background — poll GET /v1/admin/crawl/status"],
    )
