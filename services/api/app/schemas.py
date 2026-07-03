from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import LoppisStatus, ReportType, SourceType


class ScoreBreakdownOut(BaseModel):
    source_trust: float
    confirmation_count: float
    feedback_sentiment: float
    historical_accuracy: float
    freshness: float
    cancellation_penalty: float
    total: float


class LoppisSourceOut(BaseModel):
    id: UUID
    source_type: SourceType
    source_url: str
    raw_snippet: str | None
    crawled_at: datetime
    source_weight: float

    model_config = {"from_attributes": True}


class LoppisHistoryOut(BaseModel):
    id: UUID
    occurred_at: datetime
    was_accurate: bool
    photo_urls: list[str]
    attendance_signal: str | None

    model_config = {"from_attributes": True}


class LoppisSummaryOut(BaseModel):
    id: UUID
    title: str
    description: str | None
    start_at: datetime
    end_at: datetime | None
    lat: float
    lng: float
    address_text: str | None
    municipality: str | None
    county: str | None
    reliability_score: float
    status: LoppisStatus
    cover_image_url: str | None
    tags: list[str]
    source_count: int = 0


class LoppisDetailOut(LoppisSummaryOut):
    is_recurring: bool
    sources: list[LoppisSourceOut]
    history: list[LoppisHistoryOut]
    score_breakdown: ScoreBreakdownOut


class ReportIn(BaseModel):
    report_type: ReportType
    text: str | None = None


class AnonymousSessionOut(BaseModel):
    anonymous_user_id: UUID
    access_token: str
    expires_at: datetime


class FavoriteIn(BaseModel):
    loppis_id: UUID


class FavoriteOut(BaseModel):
    id: UUID
    loppis_id: UUID
    created_at: datetime
    loppis: LoppisSummaryOut | None = None

    model_config = {"from_attributes": True}


class AlertIn(BaseModel):
    loppis_id: UUID | None = None
    radius_km: float | None = Field(default=None, ge=1, le=200)
    before_hours: int = Field(default=24, ge=1, le=168)
    min_score: float = Field(default=40, ge=0, le=100)
    lat: float | None = None
    lng: float | None = None


class AlertOut(BaseModel):
    id: UUID
    loppis_id: UUID | None
    radius_km: float | None
    before_hours: int
    min_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class PushRegisterIn(BaseModel):
    push_token: str
    platform: str = "android"


class LoppisSubmitIn(BaseModel):
    title: str = Field(min_length=3, max_length=500)
    description: str | None = None
    start_at: datetime
    end_at: datetime | None = None
    address_text: str
    lat: float
    lng: float
    source_url: str | None = None
