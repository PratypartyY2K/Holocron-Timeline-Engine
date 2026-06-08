from fastapi import APIRouter, Depends, status

from app.api.dependencies.services import get_character_service
from app.engine.dto import CreateCharacterCommand
from app.engine.services.character_service import CharacterService
from app.schemas.characters import CharacterResponse, CreateCharacterRequest

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
