from dataclasses import dataclass, field

from app.domain.entities.causal_graph import CausalGraphEdge
from app.domain.entities.event import Event


@dataclass(slots=True)
class EventImpact:
    event_id: str
    impacted_events: list[Event] = field(default_factory=list)
    broken_edges: list[CausalGraphEdge] = field(default_factory=list)
