from typing import Any

from neo4j import Driver

from app.core.config import Settings
from app.domain.entities.planet import Planet
from app.repositories.interfaces.planet_repository import PlanetRepository
from app.repositories.neo4j.base import Neo4jRepositoryBase
from app.repositories.neo4j.mappers import map_planet_record


class Neo4jPlanetRepository(Neo4jRepositoryBase, PlanetRepository):
    def __init__(self, driver: Driver, settings: Settings) -> None:
        super().__init__(driver, settings)

    def create(self, planet: Planet) -> Planet:
        query = """
        CREATE (p:Planet {
            id: $id,
            slug: $slug,
            name: $name,
            description: $description,
            region: $region,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        RETURN properties(p) AS planet
        """
        record = self._execute_write("planet.create", self._create_tx, query, planet)
        return map_planet_record(record)

    def get_by_slug(self, slug: str) -> Planet | None:
        query = """
        MATCH (p:Planet {slug: $slug})
        RETURN properties(p) AS planet
        """
        record = self._run_single(query_name="planet.get_by_slug", query=query, slug=slug)
        if record is None:
            return None
        return map_planet_record(dict(record["planet"]))

    def list_planets(self) -> list[Planet]:
        query = """
        MATCH (p:Planet)
        RETURN properties(p) AS planet
        ORDER BY p.name ASC
        """
        result = self._run_result(query_name="planet.list", query=query)
        return [map_planet_record(dict(record["planet"])) for record in result]

    @staticmethod
    def _create_tx(tx: Any, query: str, planet: Planet) -> dict[str, Any]:
        record = tx.run(
            query,
            id=planet.id,
            slug=planet.slug,
            name=planet.name,
            description=planet.description,
            region=planet.region,
            created_at=planet.created_at.isoformat(),
            updated_at=planet.updated_at.isoformat(),
        ).single()
        if record is None:
            raise RuntimeError("Failed to create planet")
        return dict(record["planet"])
