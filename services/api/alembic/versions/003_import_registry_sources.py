"""Revision 003: import crawl sources from discovered_sources.json registry."""

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from app.services.source_registry_sync import load_registry_sources

    calendar_sites, facebook_groups = load_registry_sources()
    conn = op.get_bind()

    for site in calendar_sites:
        row = conn.execute(
            sa.text("SELECT id, pages FROM crawl_feed_source WHERE url = :url"),
            {"url": site["url"]},
        ).first()
        pages = site["pages"] or ["/"]
        if row:
            merged = sorted(set(row.pages or []) | set(pages))
            if merged != sorted(set(row.pages or [])):
                conn.execute(
                    sa.text("UPDATE crawl_feed_source SET pages = :pages WHERE id = :id"),
                    {"pages": merged, "id": row.id},
                )
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO crawl_feed_source (id, name, url, kind, pages, enabled)
                VALUES (:id, :name, :url, 'calendar', :pages, true)
                """
            ),
            {
                "id": uuid.uuid4(),
                "name": site["name"],
                "url": site["url"],
                "pages": pages,
            },
        )

    for group_url in facebook_groups:
        clean = group_url.split("?")[0].rstrip("/")
        exists = conn.execute(
            sa.text("SELECT 1 FROM crawl_feed_source WHERE url = :url"),
            {"url": clean},
        ).first()
        if exists:
            continue
        name = clean.rsplit("/", 1)[-1] or "facebook-group"
        conn.execute(
            sa.text(
                """
                INSERT INTO crawl_feed_source (id, name, url, kind, enabled)
                VALUES (:id, :name, :url, 'facebook_group', true)
                """
            ),
            {"id": uuid.uuid4(), "name": name, "url": clean},
        )


def downgrade() -> None:
    pass
