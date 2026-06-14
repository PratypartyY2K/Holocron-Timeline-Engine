from fastapi import APIRouter, Depends

from app.api.dependencies.services import get_timeline_simulation_service
from app.engine.services.timeline_simulation_service import TimelineSimulationService
from app.schemas.events import EventResponse, TimelineBreakSimulationResponse

router = APIRouter()


@router.get("/simulate-break/{event_id}", response_model=TimelineBreakSimulationResponse)
def simulate_break(
    event_id: str,
    service: TimelineSimulationService = Depends(get_timeline_simulation_service),
) -> TimelineBreakSimulationResponse:
    simulation = service.simulate_break(event_id)
    return TimelineBreakSimulationResponse(
        broken_event_id=simulation.broken_event_id,
        nodes=[
            {
                **EventResponse.model_validate(node.event).model_dump(),
                "status": node.status,
                "topological_rank": node.topological_rank,
                "affected_by_event_ids": node.affected_by_event_ids,
                "surviving_dependency_count": node.surviving_dependency_count,
                "broken_dependency_count": node.broken_dependency_count,
                "unresolved_dependency_count": node.unresolved_dependency_count,
            }
            for node in simulation.nodes
        ],
        edges=[edge for edge in simulation.edges],
        topological_order=simulation.topological_order,
    )
