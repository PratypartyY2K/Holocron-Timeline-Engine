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
class CreateCharacterCommand:
    slug: str
    name: str
    description: str | None
    species: str | None
    homeworld_name: str | None


@dataclass(slots=True, frozen=True)
class CreatePlanetCommand:
    slug: str
    name: str
    description: str | None
    region: str | None


@dataclass(slots=True, frozen=True)
class CreateFactionCommand:
    slug: str
    name: str
    description: str | None


@dataclass(slots=True, frozen=True)
class CreateRelationshipCommand:
    type: RelationshipType
    from_node_id: str
    to_node_id: str
    note: str | None
    subject_node_id: str | None = None
    artifact_key: str | None = None
    value_bool: bool | None = None
    value_text: str | None = None


@dataclass(slots=True, frozen=True)
class ListEventsQuery:
    start_year: int | None = None
    end_year: int | None = None
    era: str | None = None
    character: str | None = None
    location: str | None = None
    causal_depth: int | None = None
    limit: int = 50
    offset: int = 0
    order: str = "asc"
