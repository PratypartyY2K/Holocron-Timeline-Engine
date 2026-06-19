import pytest

from app.domain.entities.causal_graph import CausalGraphEdge
from app.domain.entities.event import Event
from app.domain.entities.timeline_break_simulation import (
    TimelineBreakSimulationGraph,
    TimelineNodeStatus,
)
from app.domain.enums import RelationshipType
from app.domain.errors import EntityNotFoundError
from app.engine.services.timeline_simulation_service import TimelineSimulationService
from tests.unit.engine.fakes import FakeEventRepository


def test_simulate_break_raises_when_event_is_missing() -> None:
    service = TimelineSimulationService(FakeEventRepository())

    with pytest.raises(EntityNotFoundError):
        service.simulate_break("missing")


def test_simulate_break_invalidates_entire_downstream_chain() -> None:
    repository = FakeEventRepository()
    broken = _event("event-a", "Order 66", -19)
    first = _event("event-b", "Purge Begins", -19)
    second = _event("event-c", "Jedi Underground", -18)
    for event in (broken, first, second):
        repository.create(event)

    repository.break_simulation_graphs[broken.id] = TimelineBreakSimulationGraph(
        broken_event_id=broken.id,
        downstream_events=[first, second],
        internal_edges=[
            _edge("edge-ab", broken.id, first.id),
            _edge("edge-bc", first.id, second.id),
        ],
        dependency_ids_by_event_id={
            first.id: [broken.id],
            second.id: [first.id],
        },
    )

    simulation = TimelineSimulationService(repository).simulate_break(broken.id)
    nodes_by_id = {node.event.id: node for node in simulation.nodes}

    assert simulation.topological_order == [broken.id, first.id, second.id]
    assert nodes_by_id[broken.id].status is TimelineNodeStatus.BROKEN
    assert nodes_by_id[first.id].status is TimelineNodeStatus.INVALIDATED
    assert nodes_by_id[second.id].status is TimelineNodeStatus.INVALIDATED
    assert nodes_by_id[second.id].affected_by_event_ids == [first.id]


def test_simulate_break_marks_nodes_unresolved_when_other_support_remains() -> None:
    repository = FakeEventRepository()
    broken = _event("event-a", "Death Star Plans Lost", -1)
    consequence = _event("event-b", "Battle Station Delay", 0)
    repository.create(broken)
    repository.create(consequence)

    repository.break_simulation_graphs[broken.id] = TimelineBreakSimulationGraph(
        broken_event_id=broken.id,
        downstream_events=[consequence],
        internal_edges=[_edge("edge-ab", broken.id, consequence.id)],
        dependency_ids_by_event_id={
            consequence.id: [broken.id, "external-event"],
        },
    )

    simulation = TimelineSimulationService(repository).simulate_break(broken.id)
    simulated_node = next(node for node in simulation.nodes if node.event.id == consequence.id)

    assert simulated_node.status is TimelineNodeStatus.UNRESOLVED
    assert simulated_node.surviving_dependency_count == 1
    assert simulated_node.broken_dependency_count == 1
    assert simulated_node.affected_by_event_ids == [broken.id]


def test_simulate_break_propagates_unresolved_status() -> None:
    repository = FakeEventRepository()
    broken = _event("event-a", "Temple Bombing", -19)
    unresolved = _event("event-b", "Emergency Council", -19)
    downstream = _event("event-c", "Separatist Fallout", -19)
    for event in (broken, unresolved, downstream):
        repository.create(event)

    repository.break_simulation_graphs[broken.id] = TimelineBreakSimulationGraph(
        broken_event_id=broken.id,
        downstream_events=[unresolved, downstream],
        internal_edges=[
            _edge("edge-ab", broken.id, unresolved.id),
            _edge("edge-bc", unresolved.id, downstream.id),
        ],
        dependency_ids_by_event_id={
            unresolved.id: [broken.id, "external-event"],
            downstream.id: [unresolved.id],
        },
    )

    simulation = TimelineSimulationService(repository).simulate_break(broken.id)
    nodes_by_id = {node.event.id: node for node in simulation.nodes}

    assert nodes_by_id[unresolved.id].status is TimelineNodeStatus.UNRESOLVED
    assert nodes_by_id[downstream.id].status is TimelineNodeStatus.UNRESOLVED
    assert nodes_by_id[downstream.id].unresolved_dependency_count == 1
    assert nodes_by_id[downstream.id].affected_by_event_ids == [unresolved.id]


def _event(event_id: str, title: str, start_year: int) -> Event:
    return Event(
        id=event_id,
        slug=title.casefold().replace(" ", "-"),
        title=title,
        description=None,
        start_year=start_year,
        end_year=start_year,
        era=None,
        canon_status=None,
    )


def _edge(edge_id: str, source_id: str, target_id: str) -> CausalGraphEdge:
    return CausalGraphEdge(
        id=edge_id,
        source_id=source_id,
        target_id=target_id,
        type=RelationshipType.CAUSES,
        note=None,
    )
