from dataclasses import dataclass, field
from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Event:
    id: str
    slug: str
    title: str
    description: str | None
    start_year: int
    end_year: int | None
    era: str | None
    canon_status: str | None
    source_refs: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

