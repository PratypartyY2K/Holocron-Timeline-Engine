from dataclasses import dataclass, field

from app.domain.enums import RelationshipType


@dataclass(slots=True, frozen=True)
class CreateEventCommand:
    slug: str
    title: str
    description: str | None
    start_year: int
    end_year: int | None
    era: str | None
    canon_status: str | None
    source_refs: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class CreateRelationshipCommand:
    type: RelationshipType
    from_node_id: str
    to_node_id: str
    note: str | None


@dataclass(slots=True, frozen=True)
class ListEventsQuery:
    start_year: int | None = None
    end_year: int | None = None
    limit: int = 50
    offset: int = 0
    order: str = "asc"

