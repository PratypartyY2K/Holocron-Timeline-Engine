from dataclasses import dataclass, field

from app.domain.entities.event import Event
from app.domain.enums import RelationshipType


@dataclass(slots=True, frozen=True)
class CausalGraphEdge:
    id: str
    source_id: str
    target_id: str
    type: RelationshipType
    note: str | None


@dataclass(slots=True)
class CausalGraph:
    focus_event_id: str
    depth: int
    nodes: list[Event] = field(default_factory=list)
    edges: list[CausalGraphEdge] = field(default_factory=list)
