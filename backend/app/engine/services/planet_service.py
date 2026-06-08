from uuid import uuid4

from app.domain.entities.planet import Planet
from app.domain.errors import DuplicateEntityError, ValidationError
from app.engine.dto import CreatePlanetCommand
from app.repositories.interfaces.planet_repository import PlanetRepository


class PlanetService:
    def __init__(self, planet_repository: PlanetRepository) -> None:
        self._planet_repository = planet_repository

    def create_planet(self, command: CreatePlanetCommand) -> Planet:
        if not command.slug.strip():
            raise ValidationError("slug must not be empty")
        if not command.name.strip():
            raise ValidationError("name must not be empty")
        if self._planet_repository.get_by_slug(command.slug) is not None:
            raise DuplicateEntityError(f"Planet slug already exists: {command.slug}")

        planet = Planet(
            id=str(uuid4()),
            slug=command.slug,
            name=command.name,
            description=command.description,
            region=command.region,
        )
        return self._planet_repository.create(planet)
