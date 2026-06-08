from typing import Any

from neo4j import Driver

from app.core.config import Settings
from app.domain.entities.faction import Faction
from app.repositories.interfaces.faction_repository import FactionRepository
from app.repositories.neo4j.mappers import map_faction_record


class Neo4jFactionRepository(FactionRepository):
    def __init__(self, driver: Driver, settings: Settings) -> None:
        self._driver = driver
        self._database = settings.neo4j_database

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
        with self._driver.session(database=self._database) as session:
            record = session.execute_write(self._create_tx, query, faction)
        return map_faction_record(record)

    def get_by_slug(self, slug: str) -> Faction | None:
        query = """
        MATCH (f:Faction {slug: $slug})
        RETURN properties(f) AS faction
        """
        with self._driver.session(database=self._database) as session:
            record = session.run(query, slug=slug).single()
        if record is None:
            return None
        return map_faction_record(dict(record["faction"]))

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
