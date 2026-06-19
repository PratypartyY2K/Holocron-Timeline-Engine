from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.services import get_event_service, get_universe_state_service
from app.engine.dto import CreateEventCommand, ListEventsQuery
from app.engine.services.event_service import EventService
from app.engine.services.universe_state_service import UniverseStateService
from app.schemas.events import (
    CausalGraphResponse,
    CreateEventRequest,
    EventImpactResponse,
    EventListResponse,
    EventResponse,
)
from app.schemas.universe_state import UniverseStateResponse

router = APIRouter()


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    request: CreateEventRequest,
    service: EventService = Depends(get_event_service),
) -> EventResponse:
    event = service.create_event(
        CreateEventCommand(
            slug=request.slug,
            title=request.title,
            description=request.description,
            start_year=request.start_year,
            end_year=request.end_year,
            era=request.era,
            canon_status=request.canon_status,
            source_refs=request.source_refs,
        )
    )
    return EventResponse.model_validate(event)


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: str,
    service: EventService = Depends(get_event_service),
) -> EventResponse:
    return EventResponse.model_validate(service.get_event(event_id))


@router.get("/by-slug/{slug}", response_model=EventResponse)
def get_event_by_slug(
    slug: str,
    service: EventService = Depends(get_event_service),
) -> EventResponse:
    return EventResponse.model_validate(service.get_event_by_slug(slug))


@router.get("", response_model=EventListResponse)
def list_events(
    start_year: int | None = Query(default=None),
    end_year: int | None = Query(default=None),
    era: str | None = Query(default=None),
    character: str | None = Query(default=None),
    location: str | None = Query(default=None),
    causal_depth: int | None = Query(default=None, ge=1, le=8),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    service: EventService = Depends(get_event_service),
) -> EventListResponse:
    events, total = service.list_events(
        ListEventsQuery(
            start_year=start_year,
            end_year=end_year,
            era=era,
            character=character,
            location=location,
            causal_depth=causal_depth,
            limit=limit,
            offset=offset,
            order=order,
        )
    )
    return EventListResponse(
        items=[EventResponse.model_validate(item) for item in events],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{event_id}/dependencies", response_model=list[EventResponse])
def list_dependencies(
    event_id: str,
    depth: int | None = Query(default=None, ge=1),
    service: EventService = Depends(get_event_service),
) -> list[EventResponse]:
    return [
        EventResponse.model_validate(item)
        for item in service.list_dependencies(event_id, depth=depth)
    ]


@router.get("/{event_id}/consequences", response_model=list[EventResponse])
def list_consequences(
    event_id: str,
    depth: int | None = Query(default=None, ge=1),
    service: EventService = Depends(get_event_service),
) -> list[EventResponse]:
    return [
        EventResponse.model_validate(item)
        for item in service.list_consequences(event_id, depth=depth)
    ]


@router.get("/{event_id}/causal-graph", response_model=CausalGraphResponse)
def get_causal_graph(
    event_id: str,
    depth: int = Query(default=2, ge=1, le=8),
    service: EventService = Depends(get_event_service),
) -> CausalGraphResponse:
    graph = service.get_causal_graph(event_id, depth=depth)
    return CausalGraphResponse(
        focus_event_id=graph.focus_event_id,
        depth=graph.depth,
        nodes=[EventResponse.model_validate(node) for node in graph.nodes],
        edges=[edge for edge in graph.edges],
    )


@router.get("/{event_id}/impact", response_model=EventImpactResponse)
def get_event_impact(
    event_id: str,
    service: EventService = Depends(get_event_service),
) -> EventImpactResponse:
    impact = service.get_impact(event_id)
    return EventImpactResponse(
        event_id=impact.event_id,
        impacted_events=[EventResponse.model_validate(item) for item in impact.impacted_events],
        broken_edges=[edge for edge in impact.broken_edges],
    )


@router.get("/{event_id}/universe-state", response_model=UniverseStateResponse)
def get_universe_state(
    event_id: str,
    service: UniverseStateService = Depends(get_universe_state_service),
) -> UniverseStateResponse:
    return UniverseStateResponse.model_validate(service.get_state_before_event(event_id))
