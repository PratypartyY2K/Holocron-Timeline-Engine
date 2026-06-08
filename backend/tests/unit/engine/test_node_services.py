import pytest

from app.domain.entities.character import Character
from app.domain.entities.faction import Faction
from app.domain.entities.planet import Planet
from app.domain.errors import DuplicateEntityError, ValidationError
from app.engine.dto import CreateCharacterCommand, CreateFactionCommand, CreatePlanetCommand
from app.engine.services.character_service import CharacterService
from app.engine.services.faction_service import FactionService
from app.engine.services.planet_service import PlanetService
from tests.unit.engine.fakes import (
    FakeCharacterRepository,
    FakeFactionRepository,
    FakePlanetRepository,
)


def test_create_character_persists_to_repository() -> None:
    repository = FakeCharacterRepository()
    service = CharacterService(repository)

    character = service.create_character(
        CreateCharacterCommand(
            slug="luke-skywalker",
            name="Luke Skywalker",
            description="Jedi Knight",
            species="Human",
            homeworld_name="Tatooine",
        )
    )

    assert repository.get_by_slug(character.slug) == character


def test_create_character_rejects_duplicate_slug() -> None:
    repository = FakeCharacterRepository()
    repository.create(
        Character(
            id="character-1",
            slug="luke-skywalker",
            name="Luke Skywalker",
            description=None,
            species=None,
            homeworld_name=None,
        )
    )
    service = CharacterService(repository)

    with pytest.raises(DuplicateEntityError):
        service.create_character(
            CreateCharacterCommand(
                slug="luke-skywalker",
                name="Luke",
                description=None,
                species=None,
                homeworld_name=None,
            )
        )


def test_create_planet_persists_to_repository() -> None:
    repository = FakePlanetRepository()
    service = PlanetService(repository)

    planet = service.create_planet(
        CreatePlanetCommand(
            slug="tatooine",
            name="Tatooine",
            description="Desert world",
            region="Outer Rim",
        )
    )

    assert repository.get_by_slug(planet.slug) == planet


def test_create_planet_rejects_duplicate_slug() -> None:
    repository = FakePlanetRepository()
    repository.create(
        Planet(
            id="planet-1",
            slug="tatooine",
            name="Tatooine",
            description=None,
            region=None,
        )
    )
    service = PlanetService(repository)

    with pytest.raises(DuplicateEntityError):
        service.create_planet(
            CreatePlanetCommand(
                slug="tatooine",
                name="Tatooine Prime",
                description=None,
                region=None,
            )
        )


def test_create_faction_persists_to_repository() -> None:
    repository = FakeFactionRepository()
    service = FactionService(repository)

    faction = service.create_faction(
        CreateFactionCommand(
            slug="rebel-alliance",
            name="Rebel Alliance",
            description="Opposes the Empire",
        )
    )

    assert repository.get_by_slug(faction.slug) == faction


def test_create_faction_rejects_duplicate_slug() -> None:
    repository = FakeFactionRepository()
    repository.create(
        Faction(
            id="faction-1",
            slug="rebel-alliance",
            name="Rebel Alliance",
            description=None,
        )
    )
    service = FactionService(repository)

    with pytest.raises(DuplicateEntityError):
        service.create_faction(
            CreateFactionCommand(
                slug="rebel-alliance",
                name="Alliance to Restore the Republic",
                description=None,
            )
        )


def test_create_character_rejects_blank_slug() -> None:
    service = CharacterService(FakeCharacterRepository())

    with pytest.raises(ValidationError):
        service.create_character(
            CreateCharacterCommand(
                slug=" ",
                name="Luke Skywalker",
                description=None,
                species=None,
                homeworld_name=None,
            )
        )


def test_create_planet_rejects_blank_name() -> None:
    service = PlanetService(FakePlanetRepository())

    with pytest.raises(ValidationError):
        service.create_planet(
            CreatePlanetCommand(
                slug="tatooine",
                name=" ",
                description=None,
                region=None,
            )
        )


def test_create_faction_rejects_blank_slug() -> None:
    service = FactionService(FakeFactionRepository())

    with pytest.raises(ValidationError):
        service.create_faction(
            CreateFactionCommand(
                slug=" ",
                name="Rebel Alliance",
                description=None,
            )
        )
