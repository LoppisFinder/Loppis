"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-07-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "loppis",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True)),
        sa.Column("is_recurring", sa.Boolean(), server_default="false"),
        sa.Column("recurrence_rule", sa.String(200)),
        sa.Column("location", Geography(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("address_text", sa.String(500)),
        sa.Column("municipality", sa.String(200)),
        sa.Column("county", sa.String(200)),
        sa.Column("reliability_score", sa.Float(), server_default="0"),
        sa.Column("status", sa.Enum("upcoming", "cancelled", "past", "unverified", name="loppis_status"), server_default="unverified"),
        sa.Column("cover_image_url", sa.String(1000)),
        sa.Column("tags", postgresql.ARRAY(sa.String())),
        sa.Column("last_confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_loppis_start_at", "loppis", ["start_at"])
    op.create_index("ix_loppis_reliability_score", "loppis", ["reliability_score"])
    op.create_index("ix_loppis_status", "loppis", ["status"])

    op.create_table(
        "anonymous_user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("preferences_json", sa.Text(), server_default="{}"),
    )

    op.create_table(
        "loppis_source",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loppis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("loppis.id", ondelete="CASCADE")),
        sa.Column("source_type", sa.Enum("facebook", "instagram", "reddit", "forum", "website", "user_submission", name="source_type"), nullable=False),
        sa.Column("source_url", sa.String(2000), nullable=False),
        sa.Column("raw_snippet", sa.Text()),
        sa.Column("crawled_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("source_weight", sa.Float(), server_default="50"),
    )
    op.create_index("ix_loppis_source_loppis_id", "loppis_source", ["loppis_id"])

    op.create_table(
        "loppis_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loppis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("loppis.id", ondelete="CASCADE")),
        sa.Column("sentiment", sa.Float(), server_default="0"),
        sa.Column("text", sa.Text()),
        sa.Column("author_hash", sa.String(64)),
        sa.Column("reporter_anonymous_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("anonymous_user.id", ondelete="SET NULL")),
        sa.Column("report_type", sa.Enum("cancelled", "wrong_date", "wrong_location", "spam", "other", name="report_type")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_loppis_feedback_loppis_id", "loppis_feedback", ["loppis_id"])

    op.create_table(
        "loppis_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loppis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("loppis.id", ondelete="CASCADE")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("was_accurate", sa.Boolean(), server_default="true"),
        sa.Column("photo_urls", postgresql.ARRAY(sa.String())),
        sa.Column("attendance_signal", sa.String(200)),
    )
    op.create_index("ix_loppis_history_loppis_id", "loppis_history", ["loppis_id"])

    op.create_table(
        "user_favorite",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("anonymous_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("anonymous_user.id", ondelete="CASCADE")),
        sa.Column("loppis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("loppis.id", ondelete="CASCADE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("anonymous_user_id", "loppis_id", name="uq_favorite_user_loppis"),
    )
    op.create_index("ix_user_favorite_anonymous_user_id", "user_favorite", ["anonymous_user_id"])

    op.create_table(
        "user_alert",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("anonymous_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("anonymous_user.id", ondelete="CASCADE")),
        sa.Column("loppis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("loppis.id", ondelete="CASCADE")),
        sa.Column("radius_km", sa.Float()),
        sa.Column("before_hours", sa.Integer(), server_default="24"),
        sa.Column("min_score", sa.Float(), server_default="40"),
        sa.Column("lat", sa.Float()),
        sa.Column("lng", sa.Float()),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_user_alert_anonymous_user_id", "user_alert", ["anonymous_user_id"])

    op.create_table(
        "push_device",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("anonymous_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("anonymous_user.id", ondelete="CASCADE")),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("platform", sa.String(20), server_default="android"),
        sa.Column("registered_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_push_device_anonymous_user_id", "push_device", ["anonymous_user_id"])


def downgrade() -> None:
    op.drop_table("push_device")
    op.drop_table("user_alert")
    op.drop_table("user_favorite")
    op.drop_table("loppis_history")
    op.drop_table("loppis_feedback")
    op.drop_table("loppis_source")
    op.drop_table("anonymous_user")
    op.drop_table("loppis")
    op.execute("DROP TYPE IF EXISTS report_type")
    op.execute("DROP TYPE IF EXISTS source_type")
    op.execute("DROP TYPE IF EXISTS loppis_status")
