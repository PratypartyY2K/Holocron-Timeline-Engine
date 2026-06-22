from fastapi import APIRouter, Depends, status

from app.api.dependencies.services import get_faction_service
from app.engine.dto import CreateFactionCommand
from app.engine.services.faction_service import FactionService
from app.schemas.characters import CharacterResponse
from app.schemas.events import EventResponse
from app.schemas.factions import CreateFactionRequest, FactionDetailResponse, FactionResponse

router = APIRouter()


@router.post("", response_model=FactionResponse, status_code=status.HTTP_201_CREATED)
def create_faction(
    request: CreateFactionRequest,
    service: FactionService = Depends(get_faction_service),
) -> FactionResponse:
    faction = service.create_faction(
        CreateFactionCommand(
            slug=request.slug,
            name=request.name,
            description=request.description,
        )
    )
    return FactionResponse.model_validate(faction)


@router.get("", response_model=list[FactionResponse])
def list_factions(
    service: FactionService = Depends(get_faction_service),
) -> list[FactionResponse]:
    return [FactionResponse.model_validate(faction) for faction in service.list_factions()]


@router.get("/by-slug/{slug}", response_model=FactionResponse)
def get_faction_by_slug(
    slug: str,
    service: FactionService = Depends(get_faction_service),
) -> FactionResponse:
    return FactionResponse.model_validate(service.get_faction_by_slug(slug))


@router.get("/by-slug/{slug}/detail", response_model=FactionDetailResponse)
def get_faction_detail_by_slug(
    slug: str,
    service: FactionService = Depends(get_faction_service),
) -> FactionDetailResponse:
    faction = service.get_faction_by_slug(slug)
    return FactionDetailResponse(
        faction=FactionResponse.model_validate(faction),
        characters=[CharacterResponse.model_validate(item) for item in service.list_related_characters(slug)],
        enemy_factions=[FactionResponse.model_validate(item) for item in service.list_enemy_factions(slug)],
        involved_events=[EventResponse.model_validate(item) for item in service.list_involved_events(slug)],
    )
