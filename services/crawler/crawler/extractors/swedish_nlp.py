"""Swedish date and location extraction from loppis posts."""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from dateutil import parser as date_parser

MONTHS_SV = {
    "januari": 1, "februari": 2, "mars": 3, "april": 4,
    "maj": 5, "juni": 6, "juli": 7, "augusti": 8,
    "september": 9, "oktober": 10, "november": 11, "december": 12,
}
WEEKDAYS_SV = {
    "måndag": 0, "tisdag": 1, "onsdag": 2, "torsdag": 3,
    "fredag": 4, "lördag": 5, "söndag": 6,
}

DATE_PATTERNS = [
    re.compile(r"(\d{1,2})[\./](\d{1,2})(?:[\./](\d{2,4}))?", re.IGNORECASE),
    re.compile(r"(\d{1,2})\s+(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)", re.IGNORECASE),
    re.compile(r"(måndag|tisdag|onsdag|torsdag|fredag|lördag|söndag)\s+(\d{1,2})[\./](\d{1,2})", re.IGNORECASE),
    re.compile(r"vecka\s+(\d{1,2})", re.IGNORECASE),
]

LOCATION_PATTERNS = [
    re.compile(r"(?:adress|plats|ställe)[:\s]+(.{5,80})", re.IGNORECASE),
    re.compile(r"(\d{3}\s?\d{2}\s?[A-Za-zÅÄÖåäö]+(?:,\s*[A-Za-zÅÄÖåäö\s]+)?)"),
]

MUNICIPALITIES = [
    "Stockholm", "Göteborg", "Malmö", "Uppsala", "Linköping", "Örebro",
    "Västerås", "Helsingborg", "Jönköping", "Norrköping", "Lund", "Umeå",
    "Luleå", "Sundsvall", "Gävle", "Karlstad", "Växjö", "Halmstad", "Borås",
    "Täby", "Botkyrka", "Kalmar", "Kristianstad", "Östersund", "Falun", "Skövde",
    "Södertälje", "Eskilstuna", "Visby", "Kiruna",
]


@dataclass
class ExtractedListing:
    title: str
    description: str | None
    start_at: datetime | None
    address_text: str | None
    municipality: str | None
    source_url: str
    source_type: str
    raw_snippet: str


def extract_date(text: str, reference: datetime | None = None) -> datetime | None:
    reference = reference or datetime.now(timezone.utc)
    text_lower = text.lower()

    for pattern in DATE_PATTERNS:
        match = pattern.search(text_lower)
        if not match:
            continue
        groups = match.groups()
        try:
            if "vecka" in pattern.pattern:
                week = int(groups[0])
                return reference + timedelta(weeks=week - reference.isocalendar()[1])
            if len(groups) == 3 and groups[0] in WEEKDAYS_SV:
                day, month = int(groups[1]), int(groups[2])
                year = reference.year
                dt = datetime(year, month, day, 10, 0, tzinfo=timezone.utc)
                if dt < reference:
                    dt = dt.replace(year=year + 1)
                return dt
            if len(groups) >= 2 and groups[1] in MONTHS_SV:
                day = int(groups[0])
                month = MONTHS_SV[groups[1]]
                year = reference.year
                dt = datetime(year, month, day, 10, 0, tzinfo=timezone.utc)
                if dt < reference:
                    dt = dt.replace(year=year + 1)
                return dt
            if groups[0].isdigit() and groups[1].isdigit():
                day, month = int(groups[0]), int(groups[1])
                year = int(groups[2]) if groups[2] else reference.year
                if year < 100:
                    year += 2000
                return datetime(year, month, day, 10, 0, tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue

    try:
        return date_parser.parse(text, fuzzy=True, default=reference)
    except (ValueError, OverflowError):
        return None


def extract_location(text: str) -> tuple[str | None, str | None]:
    for pattern in LOCATION_PATTERNS:
        match = pattern.search(text)
        if match:
            address = match.group(1).strip()
            municipality = next((m for m in MUNICIPALITIES if m.lower() in text.lower()), None)
            return address, municipality
    municipality = next((m for m in MUNICIPALITIES if m.lower() in text.lower()), None)
    return None, municipality


def extract_listing(title: str, body: str, source_url: str, source_type: str) -> ExtractedListing:
    combined = f"{title}\n{body}"
    start_at = extract_date(combined)
    address, municipality = extract_location(combined)
    return ExtractedListing(
        title=title[:500],
        description=body[:2000] if body else None,
        start_at=start_at,
        address_text=address,
        municipality=municipality,
        source_url=source_url,
        source_type=source_type,
        raw_snippet=body[:500] if body else None,
    )
