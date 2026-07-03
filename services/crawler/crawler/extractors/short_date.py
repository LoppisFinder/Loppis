"""Parse Swedish short dates like 4/7 or 12/7 from calendar link titles."""

import re
from datetime import datetime, timezone

SHORT_DATE = re.compile(
    r"^(\d{1,2})[\./](\d{1,2})(?:[\./](\d{2,4}))?\s+(.+)$",
    re.IGNORECASE,
)


def parse_short_date_title(
    text: str,
    reference: datetime | None = None,
    *,
    keep_current_year: bool = False,
) -> tuple[datetime | None, str]:
    """Return (start_at, title_without_date) from strings like '4/7 Loppis på Karlaplan'."""
    reference = reference or datetime.now(timezone.utc)
    text = text.strip().rstrip(">").strip()
    match = SHORT_DATE.match(text)
    if not match:
        return None, text

    day, month = int(match.group(1)), int(match.group(2))
    year = int(match.group(3)) if match.group(3) else reference.year
    if year < 100:
        year += 2000
    title = match.group(4).strip()
    try:
        dt = datetime(year, month, day, 10, 0, tzinfo=timezone.utc)
        if (
            not match.group(3)
            and not keep_current_year
            and dt < reference.replace(hour=0, minute=0, second=0, microsecond=0)
        ):
            dt = dt.replace(year=year + 1)
        return dt, title
    except ValueError:
        return None, text
