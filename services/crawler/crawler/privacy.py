"""PII stripping for crawled content."""

import re

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"(\+46|0)[\s-]?[0-9]{1,3}[\s-]?[0-9]{3,4}[\s-]?[0-9]{2,4}")
HANDLE_PATTERN = re.compile(r"@[a-zA-Z0-9_]{2,30}")
URL_PROFILE_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:facebook|instagram|twitter|x)\.com/[a-zA-Z0-9._-]+/?",
    re.IGNORECASE,
)


def strip_pii(text: str | None) -> str | None:
    if not text:
        return text
    result = text
    result = EMAIL_PATTERN.sub("[email]", result)
    result = PHONE_PATTERN.sub("[telefon]", result)
    result = HANDLE_PATTERN.sub("[användare]", result)
    result = URL_PROFILE_PATTERN.sub("[profil]", result)
    return result.strip()
