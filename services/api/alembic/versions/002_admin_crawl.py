"""Revision 002: admin crawl settings and feed sources."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FEED_SOURCE_KIND = postgresql.ENUM(
    "calendar",
    "facebook_group",
    name="feed_source_kind",
    create_type=False,
)


def upgrade() -> None:
    # Idempotent enum create (partial deploys may have created the type already)
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE feed_source_kind AS ENUM ('calendar', 'facebook_group');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    op.create_table(
        "crawl_feed_source",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("url", sa.String(2000), nullable=False),
        sa.Column("kind", FEED_SOURCE_KIND, nullable=False),
        sa.Column("pages", postgresql.ARRAY(sa.String())),
        sa.Column("enabled", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        if_not_exists=True,
    )
    op.create_index(
        "ix_crawl_feed_source_enabled",
        "crawl_feed_source",
        ["enabled"],
        if_not_exists=True,
    )

    op.create_table(
        "crawl_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("auto_enabled", sa.Boolean(), server_default="true"),
        sa.Column("interval_hours", sa.Float(), server_default="6"),
        sa.Column("auto_discover", sa.Boolean(), server_default="true"),
        sa.Column("include_search", sa.Boolean(), server_default="false"),
        sa.Column("include_social", sa.Boolean(), server_default="false"),
        sa.Column("data_version", sa.String(64), server_default="0"),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        sa.Column("last_ingested", sa.Integer(), server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        if_not_exists=True,
    )

    op.execute(
        """
        INSERT INTO crawl_settings (id, auto_enabled, interval_hours, data_version)
        VALUES (1, true, 6, '0')
        ON CONFLICT (id) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO crawl_feed_source (id, name, url, kind, pages, enabled)
        SELECT
            gen_random_uuid(),
            'loppistajm',
            'https://loppistajm.se',
            'calendar',
            ARRAY['/kalender.html', '/'],
            true
        WHERE NOT EXISTS (
            SELECT 1 FROM crawl_feed_source WHERE url = 'https://loppistajm.se'
        )
        """
    )


def downgrade() -> None:
    op.drop_table("crawl_settings")
    op.drop_index("ix_crawl_feed_source_enabled", table_name="crawl_feed_source")
    op.drop_table("crawl_feed_source")
    op.execute("DROP TYPE IF EXISTS feed_source_kind")
