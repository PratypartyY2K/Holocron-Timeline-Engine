import random
from collections import defaultdict, deque
from dataclasses import dataclass

from app.domain.entities.causal_graph import CausalGraphEdge
from app.domain.entities.event import Event
from app.domain.entities.timeline_break_simulation import (
    TimelineBreakSimulation,
    TimelineBreakSimulationGraph,
    TimelineBreakSimulationNode,
    TimelineNodeStatus,
)
from app.domain.enums import RelationshipType
from app.engine.services.timeline_simulation_service import TimelineSimulationService
from tests.unit.engine.fakes import FakeEventRepository

EVENT_COUNT = 500
GRAPH_SEED = 4517
BREAK_SELECTION_SEED = 9001


@dataclass(slots=True)
class ChaosGraphFixture:
    events_by_id: dict[str, Event]
    ranks_by_id: dict[str, int]
    children_by_id: dict[str, list[str]]
    dependencies_by_id: dict[str, list[str]]


@dataclass(slots=True)
class ExpectedSimulationNode:
    status: TimelineNodeStatus
    affected_by_event_ids: list[str]
    surviving_dependency_count: int
    broken_dependency_count: int
    unresolved_dependency_count: int


def test_chaos_simulation_predicts_downstream_states_across_large_tree() -> None:
    repository = FakeEventRepository()
    fixture = _build_chaos_fixture()
    for event in fixture.events_by_id.values():
        repository.create(event)

    service = TimelineSimulationService(repository)
    for broken_event_id in _select_break_event_ids(fixture.ranks_by_id):
        repository.break_simulation_graphs[broken_event_id] = _build_break_simulation_graph(
            fixture=fixture,
            broken_event_id=broken_event_id,
        )

        simulation = service.simulate_break(broken_event_id)

        _assert_simulation_matches_expected(
            fixture=fixture,
            broken_event_id=broken_event_id,
            simulation=simulation,
        )


def _build_chaos_fixture(event_count: int = EVENT_COUNT) -> ChaosGraphFixture:
    rng = random.Random(GRAPH_SEED)
    events_by_id: dict[str, Event] = {}
    ranks_by_id: dict[str, int] = {}
    children_by_id: dict[str, list[str]] = defaultdict(list)
    dependencies_by_id: dict[str, list[str]] = {}

    root_id = "event-0000"
    events_by_id[root_id] = _make_event(root_id, rank=0)
    ranks_by_id[root_id] = 0
    dependencies_by_id[root_id] = []
    frontier = [root_id]
    next_index = 1

    while next_index < event_count:
        next_frontier: list[str] = []
        for parent_id in frontier:
            remaining = event_count - next_index
            if remaining <= 0:
                break

            child_count = min(remaining, rng.randint(1, 3))
            for _ in range(child_count):
                event_id = f"event-{next_index:04d}"
                rank = ranks_by_id[parent_id] + 1
                dependencies = [parent_id]
                if rank >= 2 and rng.random() < 0.35:
                    dependencies.append(f"support-{event_id}")

                events_by_id[event_id] = _make_event(event_id, rank=rank)
                ranks_by_id[event_id] = rank
                children_by_id[parent_id].append(event_id)
                children_by_id.setdefault(event_id, [])
                dependencies_by_id[event_id] = dependencies
                next_frontier.append(event_id)
                next_index += 1
                if next_index >= event_count:
                    break

        frontier = next_frontier

    return ChaosGraphFixture(
        events_by_id=events_by_id,
        ranks_by_id=ranks_by_id,
        children_by_id=dict(children_by_id),
        dependencies_by_id=dependencies_by_id,
    )


def _select_break_event_ids(ranks_by_id: dict[str, int]) -> list[str]:
    rng = random.Random(BREAK_SELECTION_SEED)
    node_ids_by_rank: dict[int, list[str]] = defaultdict(list)
    for event_id, rank in ranks_by_id.items():
        node_ids_by_rank[rank].append(event_id)

    selected_ids = {"event-0000"}
    available_ranks = sorted(node_ids_by_rank)
    target_ranks = sorted(
        {
            available_ranks[0],
            available_ranks[len(available_ranks) // 4],
            available_ranks[len(available_ranks) // 2],
            available_ranks[(len(available_ranks) * 3) // 4],
            available_ranks[-1],
        }
    )
    for rank in target_ranks:
        selected_ids.add(rng.choice(sorted(node_ids_by_rank[rank])))

    weighted_pool = [
        event_id
        for rank in available_ranks
        for event_id in sorted(node_ids_by_rank[rank])
        for _ in range(rank + 1)
    ]
    while len(selected_ids) < 24:
        selected_ids.add(rng.choice(weighted_pool))

    return sorted(selected_ids, key=lambda event_id: (ranks_by_id[event_id], event_id))


def _build_break_simulation_graph(
    *,
    fixture: ChaosGraphFixture,
    broken_event_id: str,
) -> TimelineBreakSimulationGraph:
    descendant_ids = _collect_descendant_ids(
        children_by_id=fixture.children_by_id,
        root_id=broken_event_id,
    )
    downstream_ids = sorted(descendant_ids, key=lambda event_id: (fixture.ranks_by_id[event_id], event_id))
    internal_edges = [
        _make_edge(parent_id, child_id)
        for parent_id in sorted({broken_event_id, *descendant_ids})
        for child_id in sorted(fixture.children_by_id.get(parent_id, []))
        if child_id in descendant_ids
    ]

    return TimelineBreakSimulationGraph(
        broken_event_id=broken_event_id,
        downstream_events=[fixture.events_by_id[event_id] for event_id in downstream_ids],
        internal_edges=internal_edges,
        dependency_ids_by_event_id={
            event_id: list(fixture.dependencies_by_id[event_id]) for event_id in descendant_ids
        },
    )


def _collect_descendant_ids(*, children_by_id: dict[str, list[str]], root_id: str) -> set[str]:
    descendants: set[str] = set()
    stack = list(children_by_id.get(root_id, []))
    while stack:
        current_id = stack.pop()
        if current_id in descendants:
            continue
        descendants.add(current_id)
        stack.extend(children_by_id.get(current_id, []))
    return descendants


def _assert_simulation_matches_expected(
    *,
    fixture: ChaosGraphFixture,
    broken_event_id: str,
    simulation: TimelineBreakSimulation,
) -> None:
    expected_order = _build_expected_topological_order(
        children_by_id=fixture.children_by_id,
        broken_event_id=broken_event_id,
    )
    expected_nodes = _build_expected_nodes(
        dependencies_by_id=fixture.dependencies_by_id,
        topological_order=expected_order,
        broken_event_id=broken_event_id,
    )
    actual_nodes_by_id = {node.event.id: node for node in simulation.nodes}

    assert simulation.broken_event_id == broken_event_id
    assert simulation.topological_order == expected_order
    assert [node.event.id for node in simulation.nodes] == expected_order
    assert set(actual_nodes_by_id) == set(expected_nodes)

    for event_id, expected in expected_nodes.items():
        actual = actual_nodes_by_id[event_id]
        assert _node_snapshot(actual) == _expected_snapshot(expected)


def _build_expected_topological_order(
    *,
    children_by_id: dict[str, list[str]],
    broken_event_id: str,
) -> list[str]:
    included_ids = {broken_event_id, *_collect_descendant_ids(children_by_id=children_by_id, root_id=broken_event_id)}
    indegree = {event_id: 0 for event_id in included_ids}
    adjacency = {event_id: [] for event_id in included_ids}
    for parent_id in included_ids:
        for child_id in children_by_id.get(parent_id, []):
            if child_id not in included_ids:
                continue
            adjacency[parent_id].append(child_id)
            indegree[child_id] += 1

    queue = deque(sorted(event_id for event_id, degree in indegree.items() if degree == 0))
    topological_order: list[str] = []
    while queue:
        current_id = queue.popleft()
        topological_order.append(current_id)
        for child_id in sorted(adjacency[current_id]):
            indegree[child_id] -= 1
            if indegree[child_id] == 0:
                queue.append(child_id)
    return topological_order


def _build_expected_nodes(
    *,
    dependencies_by_id: dict[str, list[str]],
    topological_order: list[str],
    broken_event_id: str,
) -> dict[str, ExpectedSimulationNode]:
    expected_nodes = {
        broken_event_id: ExpectedSimulationNode(
            status=TimelineNodeStatus.BROKEN,
            affected_by_event_ids=[broken_event_id],
            surviving_dependency_count=0,
            broken_dependency_count=0,
            unresolved_dependency_count=0,
        )
    }
    statuses = {broken_event_id: TimelineNodeStatus.BROKEN}

    for event_id in topological_order[1:]:
        dependency_ids = dependencies_by_id[event_id]
        broken_dependency_ids = sorted(
            dependency_id
            for dependency_id in dependency_ids
            if statuses.get(dependency_id) in {TimelineNodeStatus.BROKEN, TimelineNodeStatus.INVALIDATED}
        )
        unresolved_dependency_ids = sorted(
            dependency_id
            for dependency_id in dependency_ids
            if statuses.get(dependency_id) is TimelineNodeStatus.UNRESOLVED
        )
        surviving_dependency_ids = sorted(
            dependency_id
            for dependency_id in dependency_ids
            if dependency_id not in statuses
            or statuses.get(dependency_id) is TimelineNodeStatus.ACTIVE
        )
        status = (
            TimelineNodeStatus.UNRESOLVED
            if surviving_dependency_ids or unresolved_dependency_ids
            else TimelineNodeStatus.INVALIDATED
        )
        statuses[event_id] = status
        expected_nodes[event_id] = ExpectedSimulationNode(
            status=status,
            affected_by_event_ids=sorted(set(broken_dependency_ids + unresolved_dependency_ids)),
            surviving_dependency_count=len(surviving_dependency_ids),
            broken_dependency_count=len(broken_dependency_ids),
            unresolved_dependency_count=len(unresolved_dependency_ids),
        )

    return expected_nodes


def _node_snapshot(node: TimelineBreakSimulationNode) -> tuple[object, ...]:
    return (
        node.status,
        node.affected_by_event_ids,
        node.surviving_dependency_count,
        node.broken_dependency_count,
        node.unresolved_dependency_count,
    )


def _expected_snapshot(node: ExpectedSimulationNode) -> tuple[object, ...]:
    return (
        node.status,
        node.affected_by_event_ids,
        node.surviving_dependency_count,
        node.broken_dependency_count,
        node.unresolved_dependency_count,
    )


def _make_event(event_id: str, *, rank: int) -> Event:
    title = f"Chaos Event {event_id}"
    start_year = rank - 1000
    return Event(
        id=event_id,
        slug=event_id,
        title=title,
        description=None,
        start_year=start_year,
        end_year=start_year,
        era=None,
        canon_status=None,
    )


def _make_edge(source_id: str, target_id: str) -> CausalGraphEdge:
    return CausalGraphEdge(
        id=f"edge-{source_id}-{target_id}",
        source_id=source_id,
        target_id=target_id,
        type=RelationshipType.CAUSES,
        note=None,
    )
