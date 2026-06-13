from fastapi import Depends

from app.core.config import Settings, get_settings
from app.db.neo4j import get_driver
from app.engine.services.character_service import CharacterService
from app.engine.services.event_service import EventService
from app.engine.services.faction_service import FactionService
from app.engine.services.planet_service import PlanetService
from app.engine.services.relationship_service import RelationshipService
from app.engine.services.search_service import SearchService
from app.engine.services.universe_state_service import UniverseStateService
from app.repositories.neo4j.character_repository import Neo4jCharacterRepository
from app.repositories.neo4j.event_repository import Neo4jEventRepository
from app.repositories.neo4j.faction_repository import Neo4jFactionRepository
from app.repositories.neo4j.graph_repository import Neo4jGraphRepository
from app.repositories.neo4j.planet_repository import Neo4jPlanetRepository


def get_event_repository(settings: Settings = Depends(get_settings)) -> Neo4jEventRepository:
    return Neo4jEventRepository(driver=get_driver(), settings=settings)


def get_character_repository(settings: Settings = Depends(get_settings)) -> Neo4jCharacterRepository:
    return Neo4jCharacterRepository(driver=get_driver(), settings=settings)


def get_planet_repository(settings: Settings = Depends(get_settings)) -> Neo4jPlanetRepository:
    return Neo4jPlanetRepository(driver=get_driver(), settings=settings)


def get_faction_repository(settings: Settings = Depends(get_settings)) -> Neo4jFactionRepository:
    return Neo4jFactionRepository(driver=get_driver(), settings=settings)


def get_graph_repository(settings: Settings = Depends(get_settings)) -> Neo4jGraphRepository:
    return Neo4jGraphRepository(driver=get_driver(), settings=settings)


def get_event_service(
    repository: Neo4jEventRepository = Depends(get_event_repository),
) -> EventService:
    return EventService(event_repository=repository)


def get_character_service(
    repository: Neo4jCharacterRepository = Depends(get_character_repository),
) -> CharacterService:
    return CharacterService(character_repository=repository)


def get_planet_service(
    repository: Neo4jPlanetRepository = Depends(get_planet_repository),
) -> PlanetService:
    return PlanetService(planet_repository=repository)


def get_faction_service(
    repository: Neo4jFactionRepository = Depends(get_faction_repository),
) -> FactionService:
    return FactionService(faction_repository=repository)


def get_relationship_service(
    repository: Neo4jGraphRepository = Depends(get_graph_repository),
) -> RelationshipService:
    return RelationshipService(graph_repository=repository)


def get_search_service(
    repository: Neo4jGraphRepository = Depends(get_graph_repository),
) -> SearchService:
    return SearchService(graph_repository=repository)


def get_universe_state_service(
    event_repository: Neo4jEventRepository = Depends(get_event_repository),
    character_repository: Neo4jCharacterRepository = Depends(get_character_repository),
    planet_repository: Neo4jPlanetRepository = Depends(get_planet_repository),
    faction_repository: Neo4jFactionRepository = Depends(get_faction_repository),
    graph_repository: Neo4jGraphRepository = Depends(get_graph_repository),
) -> UniverseStateService:
    return UniverseStateService(
        event_repository=event_repository,
        character_repository=character_repository,
        planet_repository=planet_repository,
        faction_repository=faction_repository,
        graph_repository=graph_repository,
    )
