from typing import Any

from neo4j import Driver

from app.core.config import Settings
from app.domain.entities.character import Character
from app.domain.entities.event import Event
from app.domain.entities.faction import Faction
from app.repositories.interfaces.faction_repository import FactionRepository
from app.repositories.neo4j.base import Neo4jRepositoryBase
from app.repositories.neo4j.mappers import (
    map_character_record,
    map_event_record,
    map_faction_record,
)


class Neo4jFactionRepository(Neo4jRepositoryBase, FactionRepository):
    def __init__(self, driver: Driver, settings: Settings) -> None:
        super().__init__(driver, settings)

    def create(self, faction: Faction) -> Faction:
        query = """
        CREATE (f:Faction {
            id: $id,
            slug: $slug,
            name: $name,
            description: $description,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        RETURN properties(f) AS faction
        """
        record = self._execute_write("faction.create", self._create_tx, query, faction)
        return map_faction_record(record)

    def get_by_slug(self, slug: str) -> Faction | None:
        query = """
        MATCH (f:Faction {slug: $slug})
        RETURN properties(f) AS faction
        """
        record = self._run_single(query_name="faction.get_by_slug", query=query, slug=slug)
        if record is None:
            return None
        return map_faction_record(dict(record["faction"]))

    def list_factions(self) -> list[Faction]:
        query = """
        MATCH (f:Faction)
        RETURN properties(f) AS faction
        ORDER BY f.name ASC
        """
        result = self._run_result(query_name="faction.list", query=query)
        return [map_faction_record(dict(record["faction"])) for record in result]

    def list_related_characters(self, slug: str) -> list[Character]:
        query = """
        MATCH (f:Faction {slug: $slug})<-[:INVOLVES]-(event:Event)-[:INVOLVES]->(character:Character)
        WITH character, count(DISTINCT event) AS involvement_count
        RETURN properties(character) AS character
        ORDER BY involvement_count DESC, character.name ASC
        """
        result = self._run_result(query_name="faction.list_related_characters", query=query, slug=slug)
        return [map_character_record(dict(record["character"])) for record in result]

    def list_enemy_factions(self, slug: str) -> list[Faction]:
        query = """
        MATCH (f:Faction {slug: $slug})-[:ENEMY_OF]-(enemy:Faction)
        RETURN properties(enemy) AS faction
        ORDER BY enemy.name ASC
        """
        result = self._run_result(query_name="faction.list_enemy_factions", query=query, slug=slug)
        return [map_faction_record(dict(record["faction"])) for record in result]

    def list_involved_events(self, slug: str) -> list[Event]:
        query = """
        MATCH (event:Event)-[:INVOLVES]->(f:Faction {slug: $slug})
        CALL {
            WITH event
            OPTIONAL MATCH (dependency:Event)-[:CAUSES*1..]->(event)
            RETURN count(DISTINCT dependency) AS dependency_count
        }
        CALL {
            WITH event
            OPTIONAL MATCH (incoming:Event)-[:CAUSES]->(event)
            RETURN count(DISTINCT incoming) AS incoming_degree
        }
        CALL {
            WITH event
            OPTIONAL MATCH (event)-[:CAUSES]->(outgoing:Event)
            RETURN count(DISTINCT outgoing) AS outgoing_degree
        }
        CALL {
            WITH event
            OPTIONAL MATCH (event)-[:INVOLVES]->(faction:Faction)
            RETURN
                collect(DISTINCT faction.slug) AS faction_slugs,
                collect(DISTINCT faction.name) AS faction_names
        }
        CALL {
            MATCH (all_events:Event)
            RETURN count(all_events) AS total_events
        }
        RETURN event {
            .*,
            dependency_count: dependency_count,
            centrality_score: CASE
                WHEN total_events <= 1 THEN 0.0
                ELSE toFloat(incoming_degree + outgoing_degree) / toFloat(2 * (total_events - 1))
            END,
            faction_slugs: faction_slugs,
            faction_names: faction_names
        } AS event
        ORDER BY event.start_year ASC, event.title ASC
        """
        result = self._run_result(query_name="faction.list_involved_events", query=query, slug=slug)
        return [map_event_record(dict(record["event"])) for record in result]

    @staticmethod
    def _create_tx(tx: Any, query: str, faction: Faction) -> dict[str, Any]:
        record = tx.run(
            query,
            id=faction.id,
            slug=faction.slug,
            name=faction.name,
            description=faction.description,
            created_at=faction.created_at.isoformat(),
            updated_at=faction.updated_at.isoformat(),
        ).single()
        if record is None:
            raise RuntimeError("Failed to create faction")
        return dict(record["faction"])
