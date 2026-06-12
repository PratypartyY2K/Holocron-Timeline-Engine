from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.services import get_character_service, get_event_service
from app.engine.dto import CreateCharacterCommand, ListEventsQuery
from app.engine.services.character_service import CharacterService
from app.engine.services.event_service import EventService
from app.schemas.characters import CharacterResponse, CreateCharacterRequest
from app.schemas.events import EventListResponse, EventResponse

router = APIRouter()


@router.post("", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
def create_character(
    request: CreateCharacterRequest,
    service: CharacterService = Depends(get_character_service),
) -> CharacterResponse:
    character = service.create_character(
        CreateCharacterCommand(
            slug=request.slug,
            name=request.name,
            description=request.description,
            species=request.species,
            homeworld_name=request.homeworld_name,
        )
    )
    return CharacterResponse.model_validate(character)


@router.get("", response_model=list[CharacterResponse])
def list_characters(
    service: CharacterService = Depends(get_character_service),
) -> list[CharacterResponse]:
    return [CharacterResponse.model_validate(character) for character in service.list_characters()]


@router.get("/by-slug/{slug}", response_model=CharacterResponse)
def get_character_by_slug(
    slug: str,
    service: CharacterService = Depends(get_character_service),
) -> CharacterResponse:
    return CharacterResponse.model_validate(service.get_character_by_slug(slug))


@router.get("/{character_id}/timeline", response_model=EventListResponse)
def get_character_timeline(
    character_id: str,
    start_year: int | None = Query(default=None),
    end_year: int | None = Query(default=None),
    era: str | None = Query(default=None),
    location: str | None = Query(default=None),
    causal_depth: int | None = Query(default=None, ge=1, le=8),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    character_service: CharacterService = Depends(get_character_service),
    event_service: EventService = Depends(get_event_service),
) -> EventListResponse:
    character = character_service.get_character(character_id)
    events, total = event_service.list_events(
        ListEventsQuery(
            start_year=start_year,
            end_year=end_year,
            era=era,
            character=character.slug,
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
