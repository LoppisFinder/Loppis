"""Revision 002: admin crawl settings and feed sources."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    feed_kind = sa.Enum("calendar", "facebook_group", name="feed_source_kind")
    feed_kind.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "crawl_feed_source",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("url", sa.String(2000), nullable=False),
        sa.Column("kind", feed_kind, nullable=False),
        sa.Column("pages", postgresql.ARRAY(sa.String())),
        sa.Column("enabled", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_crawl_feed_source_enabled", "crawl_feed_source", ["enabled"])

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
    )

    op.execute(
        """
        INSERT INTO crawl_settings (id, auto_enabled, interval_hours, data_version)
        VALUES (1, true, 6, '0')
        """
    )
    op.execute(
        """
        INSERT INTO crawl_feed_source (id, name, url, kind, pages, enabled)
        VALUES (
            gen_random_uuid(),
            'loppistajm',
            'https://loppistajm.se',
            'calendar',
            ARRAY['/kalender.html', '/'],
            true
        )
        """
    )


def downgrade() -> None:
    op.drop_table("crawl_settings")
    op.drop_index("ix_crawl_feed_source_enabled", table_name="crawl_feed_source")
    op.drop_table("crawl_feed_source")
    sa.Enum(name="feed_source_kind").drop(op.get_bind(), checkfirst=True)
