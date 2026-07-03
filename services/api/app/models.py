import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class LoppisStatus(str, enum.Enum):
    upcoming = "upcoming"
    cancelled = "cancelled"
    past = "past"
    unverified = "unverified"


class SourceType(str, enum.Enum):
    facebook = "facebook"
    instagram = "instagram"
    reddit = "reddit"
    forum = "forum"
    website = "website"
    user_submission = "user_submission"


class ReportType(str, enum.Enum):
    cancelled = "cancelled"
    wrong_date = "wrong_date"
    wrong_location = "wrong_location"
    spam = "spam"
    other = "other"


class Loppis(Base):
    __tablename__ = "loppis"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[str | None] = mapped_column(String(200))
    location: Mapped[str] = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    address_text: Mapped[str | None] = mapped_column(String(500))
    municipality: Mapped[str | None] = mapped_column(String(200))
    county: Mapped[str | None] = mapped_column(String(200))
    reliability_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    status: Mapped[LoppisStatus] = mapped_column(
        Enum(LoppisStatus, name="loppis_status"), default=LoppisStatus.unverified, index=True
    )
    cover_image_url: Mapped[str | None] = mapped_column(String(1000))
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    last_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sources: Mapped[list["LoppisSource"]] = relationship(back_populates="loppis", cascade="all, delete-orphan")
    feedback: Mapped[list["LoppisFeedback"]] = relationship(back_populates="loppis", cascade="all, delete-orphan")
    history: Mapped[list["LoppisHistory"]] = relationship(back_populates="loppis", cascade="all, delete-orphan")


class LoppisSource(Base):
    __tablename__ = "loppis_source"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loppis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("loppis.id", ondelete="CASCADE"), index=True)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType, name="source_type"), nullable=False)
    source_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    raw_snippet: Mapped[str | None] = mapped_column(Text)
    crawled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source_weight: Mapped[float] = mapped_column(Float, default=50.0)

    loppis: Mapped["Loppis"] = relationship(back_populates="sources")


class LoppisFeedback(Base):
    __tablename__ = "loppis_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loppis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("loppis.id", ondelete="CASCADE"), index=True)
    sentiment: Mapped[float] = mapped_column(Float, default=0.0)
    text: Mapped[str | None] = mapped_column(Text)
    author_hash: Mapped[str | None] = mapped_column(String(64))
    reporter_anonymous_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("anonymous_user.id", ondelete="SET NULL")
    )
    report_type: Mapped[ReportType | None] = mapped_column(Enum(ReportType, name="report_type"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    loppis: Mapped["Loppis"] = relationship(back_populates="feedback")


class LoppisHistory(Base):
    __tablename__ = "loppis_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loppis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("loppis.id", ondelete="CASCADE"), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    was_accurate: Mapped[bool] = mapped_column(Boolean, default=True)
    photo_urls: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    attendance_signal: Mapped[str | None] = mapped_column(String(200))

    loppis: Mapped["Loppis"] = relationship(back_populates="history")


class AnonymousUser(Base):
    __tablename__ = "anonymous_user"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    preferences_json: Mapped[str | None] = mapped_column(Text, default="{}")

    favorites: Mapped[list["UserFavorite"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    alerts: Mapped[list["UserAlert"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    push_devices: Mapped[list["PushDevice"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserFavorite(Base):
    __tablename__ = "user_favorite"
    __table_args__ = (UniqueConstraint("anonymous_user_id", "loppis_id", name="uq_favorite_user_loppis"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anonymous_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("anonymous_user.id", ondelete="CASCADE"), index=True
    )
    loppis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("loppis.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["AnonymousUser"] = relationship(back_populates="favorites")
    loppis: Mapped["Loppis"] = relationship()


class UserAlert(Base):
    __tablename__ = "user_alert"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anonymous_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("anonymous_user.id", ondelete="CASCADE"), index=True
    )
    loppis_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("loppis.id", ondelete="CASCADE"))
    radius_km: Mapped[float | None] = mapped_column(Float)
    before_hours: Mapped[int] = mapped_column(Integer, default=24)
    min_score: Mapped[float] = mapped_column(Float, default=40.0)
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["AnonymousUser"] = relationship(back_populates="alerts")


class PushDevice(Base):
    __tablename__ = "push_device"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anonymous_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("anonymous_user.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    platform: Mapped[str] = mapped_column(String(20), default="android")
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["AnonymousUser"] = relationship(back_populates="push_devices")
