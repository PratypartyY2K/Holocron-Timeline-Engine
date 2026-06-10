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
