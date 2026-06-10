from uuid import uuid4

from app.domain.entities.faction import Faction
from app.domain.errors import DuplicateEntityError, EntityNotFoundError, ValidationError
from app.engine.dto import CreateFactionCommand
from app.repositories.interfaces.faction_repository import FactionRepository


class FactionService:
    def __init__(self, faction_repository: FactionRepository) -> None:
        self._faction_repository = faction_repository

    def create_faction(self, command: CreateFactionCommand) -> Faction:
        if not command.slug.strip():
            raise ValidationError("slug must not be empty")
        if not command.name.strip():
            raise ValidationError("name must not be empty")
        if self._faction_repository.get_by_slug(command.slug) is not None:
            raise DuplicateEntityError(f"Faction slug already exists: {command.slug}")

        faction = Faction(
            id=str(uuid4()),
            slug=command.slug,
            name=command.name,
            description=command.description,
        )
        return self._faction_repository.create(faction)

    def get_faction_by_slug(self, slug: str) -> Faction:
        faction = self._faction_repository.get_by_slug(slug)
        if faction is None:
            raise EntityNotFoundError(f"Faction not found for slug: {slug}")
        return faction

    def list_factions(self) -> list[Faction]:
        return self._faction_repository.list_factions()
