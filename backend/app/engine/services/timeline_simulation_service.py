from collections import deque

from app.domain.entities.event import Event
from app.domain.entities.timeline_break_simulation import (
    TimelineBreakSimulation,
    TimelineBreakSimulationGraph,
    TimelineBreakSimulationNode,
    TimelineNodeStatus,
)
from app.domain.errors import EntityNotFoundError
from app.repositories.interfaces.event_repository import EventRepository


class TimelineSimulationService:
    def __init__(self, event_repository: EventRepository) -> None:
        self._event_repository = event_repository

    def simulate_break(self, event_id: str) -> TimelineBreakSimulation:
        broken_event = self._event_repository.get_by_id(event_id)
        if broken_event is None:
            raise EntityNotFoundError(f"Event not found: {event_id}")

        graph = self._event_repository.get_break_simulation_graph(event_id)
        return self._build_simulation(broken_event=broken_event, graph=graph)

    def _build_simulation(
        self,
        *,
        broken_event: Event,
        graph: TimelineBreakSimulationGraph,
    ) -> TimelineBreakSimulation:
        nodes_by_id = {broken_event.id: broken_event}
        nodes_by_id.update({event.id: event for event in graph.downstream_events})

        adjacency: dict[str, list[str]] = {event_id: [] for event_id in nodes_by_id}
        indegree: dict[str, int] = {event_id: 0 for event_id in nodes_by_id}
        for edge in graph.internal_edges:
            adjacency.setdefault(edge.source_id, []).append(edge.target_id)
            indegree[edge.target_id] = indegree.get(edge.target_id, 0) + 1

        queue = deque(sorted(event_id for event_id, degree in indegree.items() if degree == 0))
        topological_order: list[str] = []
        while queue:
            current = queue.popleft()
            topological_order.append(current)
            for target_id in sorted(adjacency.get(current, [])):
                indegree[target_id] -= 1
                if indegree[target_id] == 0:
                    queue.append(target_id)

        if len(topological_order) != len(nodes_by_id):
            remaining_ids = sorted(
                event_id for event_id in nodes_by_id if event_id not in topological_order
            )
            topological_order.extend(remaining_ids)

        statuses: dict[str, TimelineNodeStatus] = {broken_event.id: TimelineNodeStatus.BROKEN}
        simulation_nodes: list[TimelineBreakSimulationNode] = [
            TimelineBreakSimulationNode(
                event=broken_event,
                status=TimelineNodeStatus.BROKEN,
                topological_rank=0,
                affected_by_event_ids=[broken_event.id],
            )
        ]

        for rank, current_id in enumerate(topological_order):
            if current_id == broken_event.id:
                continue

            dependency_ids = graph.dependency_ids_by_event_id.get(current_id, [])
            broken_dependency_ids = sorted(
                dependency_id
                for dependency_id in dependency_ids
                if statuses.get(dependency_id)
                in {TimelineNodeStatus.BROKEN, TimelineNodeStatus.INVALIDATED}
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
            statuses[current_id] = status

            simulation_nodes.append(
                TimelineBreakSimulationNode(
                    event=nodes_by_id[current_id],
                    status=status,
                    topological_rank=rank,
                    affected_by_event_ids=sorted(
                        set(broken_dependency_ids + unresolved_dependency_ids)
                    ),
                    surviving_dependency_count=len(surviving_dependency_ids),
                    broken_dependency_count=len(broken_dependency_ids),
                    unresolved_dependency_count=len(unresolved_dependency_ids),
                )
            )

        simulation_nodes.sort(
            key=lambda item: (
                item.topological_rank,
                item.event.start_year,
                item.event.title,
                item.event.id,
            )
        )
        return TimelineBreakSimulation(
            broken_event_id=broken_event.id,
            nodes=simulation_nodes,
            edges=graph.internal_edges,
            topological_order=topological_order,
        )
