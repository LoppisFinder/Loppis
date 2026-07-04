"""Normalize DATABASE_URL for asyncpg (Neon/Render)."""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# libpq URL params that asyncpg does not accept via SQLAlchemy connect()
_ASYNCPG_STRIP_PARAMS = frozenset(
    {
        "sslmode",
        "channel_binding",
        "options",
        "target_session_attrs",
        "gssencmode",
    }
)

# Strip even if urlparse misses it (malformed passwords, encoding quirks)
_CHANNEL_BINDING_RE = re.compile(r"[&?]channel_binding=[^&]*", re.IGNORECASE)


def normalize_async_database_url(url: str) -> tuple[str, dict]:
    """Return asyncpg-compatible URL and connect_args."""
    url = url.strip()
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]

    # Fallback: remove channel_binding anywhere in the string before parsing
    url = _CHANNEL_BINDING_RE.sub("", url).rstrip("?&")

    parsed = urlparse(url)
    raw_query = parse_qsl(parsed.query, keep_blank_values=True)
    query: dict[str, str] = {}
    connect_args: dict = {}

    for key, value in raw_query:
        key_lower = key.lower()
        if key_lower == "sslmode":
            if value in ("require", "verify-full", "verify-ca"):
                connect_args["ssl"] = True
            continue
        if key_lower in _ASYNCPG_STRIP_PARAMS:
            continue
        query[key] = value

    if "ssl" not in connect_args and "neon.tech" in (parsed.hostname or ""):
        connect_args["ssl"] = True

    cleaned = urlunparse(parsed._replace(query=urlencode(query)))
    cleaned = _CHANNEL_BINDING_RE.sub("", cleaned).rstrip("?&")
    return cleaned, connect_args


def asyncpg_connect_args(connect_args: dict | None = None) -> dict:
    """Return connect_args safe for asyncpg.connect()."""
    args = dict(connect_args or {})
    for key in list(args):
        if key.lower() in _ASYNCPG_STRIP_PARAMS:
            args.pop(key)
    return args
