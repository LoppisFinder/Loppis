from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.crawl_admin import count_loppis, get_crawl_settings

router = APIRouter(prefix="/v1/meta", tags=["meta"])


class MetaOut(BaseModel):
    data_version: str
    last_crawl_at: str | None = None
    total_loppis: int


@router.get("", response_model=MetaOut)
async def get_meta(db: AsyncSession = Depends(get_db)):
    settings = await get_crawl_settings(db)
    total = await count_loppis(db)
    return MetaOut(
        data_version=settings.data_version,
        last_crawl_at=settings.last_run_at.isoformat() if settings.last_run_at else None,
        total_loppis=total,
    )
