from typing import Any

from neo4j import Driver

from app.core.config import Settings
from app.domain.entities.faction import Faction
from app.repositories.interfaces.faction_repository import FactionRepository
from app.repositories.neo4j.base import Neo4jRepositoryBase
from app.repositories.neo4j.mappers import map_faction_record


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
