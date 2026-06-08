from fastapi import APIRouter, Depends, status

from app.api.dependencies.services import get_faction_service
from app.engine.dto import CreateFactionCommand
from app.engine.services.faction_service import FactionService
from app.schemas.factions import CreateFactionRequest, FactionResponse

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
