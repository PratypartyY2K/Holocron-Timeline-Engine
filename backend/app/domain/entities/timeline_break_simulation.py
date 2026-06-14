from dataclasses import dataclass, field
from enum import StrEnum

from app.domain.entities.causal_graph import CausalGraphEdge
from app.domain.entities.event import Event


class TimelineNodeStatus(StrEnum):
    ACTIVE = "active"
    BROKEN = "broken"
    INVALIDATED = "invalidated"
    UNRESOLVED = "unresolved"


@dataclass(slots=True)
class TimelineBreakSimulationGraph:
    broken_event_id: str
    downstream_events: list[Event] = field(default_factory=list)
    internal_edges: list[CausalGraphEdge] = field(default_factory=list)
    dependency_ids_by_event_id: dict[str, list[str]] = field(default_factory=dict)


@dataclass(slots=True)
class TimelineBreakSimulationNode:
    event: Event
    status: TimelineNodeStatus
    topological_rank: int
    affected_by_event_ids: list[str] = field(default_factory=list)
    surviving_dependency_count: int = 0
    broken_dependency_count: int = 0
    unresolved_dependency_count: int = 0


@dataclass(slots=True)
class TimelineBreakSimulation:
    broken_event_id: str
    nodes: list[TimelineBreakSimulationNode] = field(default_factory=list)
    edges: list[CausalGraphEdge] = field(default_factory=list)
    topological_order: list[str] = field(default_factory=list)
