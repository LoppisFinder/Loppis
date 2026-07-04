"""Normalize DATABASE_URL for asyncpg (Neon/Render)."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# libpq URL params that asyncpg does not accept via SQLAlchemy connect()
_ASYNCPG_STRIP_PARAMS = (
    "sslmode",
    "channel_binding",
    "options",
    "target_session_attrs",
    "gssencmode",
)


def normalize_async_database_url(url: str) -> tuple[str, dict]:
    """Return asyncpg-compatible URL and connect_args."""
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]

    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    connect_args: dict = {}

    sslmode = query.pop("sslmode", None)
    for key in _ASYNCPG_STRIP_PARAMS:
        query.pop(key, None)

    if sslmode in ("require", "verify-full", "verify-ca") or "neon.tech" in (parsed.hostname or ""):
        connect_args["ssl"] = True

    cleaned = urlunparse(parsed._replace(query=urlencode(query)))
    return cleaned, connect_args
