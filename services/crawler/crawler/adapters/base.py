"""Base adapter protocol for loppis sources."""

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol


@dataclass
class RawListing:
    title: str
    description: str | None
    start_at: datetime | None
    address_text: str | None
    municipality: str | None
    lat: float | None
    lng: float | None
    source_url: str
    source_type: str
    raw_snippet: str | None
    external_author_id: str | None = None


class SourceAdapter(Protocol):
    source_type: str

    def discover(self) -> Iterable[RawListing]: ...

    def fetch_detail(self, url: str) -> RawListing | None: ...
