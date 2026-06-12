from uuid import uuid4

from app.domain.entities.character import Character
from app.domain.errors import DuplicateEntityError, EntityNotFoundError, ValidationError
from app.engine.dto import CreateCharacterCommand
from app.repositories.interfaces.character_repository import CharacterRepository


class CharacterService:
    def __init__(self, character_repository: CharacterRepository) -> None:
        self._character_repository = character_repository

    def create_character(self, command: CreateCharacterCommand) -> Character:
        if not command.slug.strip():
            raise ValidationError("slug must not be empty")
        if not command.name.strip():
            raise ValidationError("name must not be empty")
        if self._character_repository.get_by_slug(command.slug) is not None:
            raise DuplicateEntityError(f"Character slug already exists: {command.slug}")

        character = Character(
            id=str(uuid4()),
            slug=command.slug,
            name=command.name,
            description=command.description,
            species=command.species,
            homeworld_name=command.homeworld_name,
        )
        return self._character_repository.create(character)

    def get_character(self, character_id: str) -> Character:
        character = self._character_repository.get_by_id(character_id)
        if character is None:
            raise EntityNotFoundError(f"Character not found: {character_id}")
        return character

    def get_character_by_slug(self, slug: str) -> Character:
        character = self._character_repository.get_by_slug(slug)
        if character is None:
            raise EntityNotFoundError(f"Character not found for slug: {slug}")
        return character

    def list_characters(self) -> list[Character]:
        return self._character_repository.list_characters()
