from fastapi import APIRouter, Depends, Query

from app.api.dependencies.services import get_event_service
from app.engine.dto import ListEventsQuery
from app.engine.services.event_service import EventService
from app.schemas.events import EventListResponse, EventResponse

router = APIRouter()


@router.get("/events", response_model=EventListResponse)
def list_timeline_events(
    start_year: int | None = Query(default=None),
    end_year: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    service: EventService = Depends(get_event_service),
) -> EventListResponse:
    events, total = service.list_events(
        ListEventsQuery(
            start_year=start_year,
            end_year=end_year,
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
