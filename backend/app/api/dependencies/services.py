from fastapi import Depends

from app.core.config import Settings, get_settings
from app.db.neo4j import get_driver
from app.engine.services.event_service import EventService
from app.engine.services.relationship_service import RelationshipService
from app.repositories.neo4j.event_repository import Neo4jEventRepository
from app.repositories.neo4j.graph_repository import Neo4jGraphRepository


def get_event_repository(settings: Settings = Depends(get_settings)) -> Neo4jEventRepository:
    return Neo4jEventRepository(driver=get_driver(), settings=settings)


def get_graph_repository(settings: Settings = Depends(get_settings)) -> Neo4jGraphRepository:
    return Neo4jGraphRepository(driver=get_driver(), settings=settings)


def get_event_service(
    repository: Neo4jEventRepository = Depends(get_event_repository),
) -> EventService:
    return EventService(event_repository=repository)


def get_relationship_service(
    repository: Neo4jGraphRepository = Depends(get_graph_repository),
) -> RelationshipService:
    return RelationshipService(graph_repository=repository)

