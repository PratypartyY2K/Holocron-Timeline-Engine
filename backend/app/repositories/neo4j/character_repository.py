from typing import Any

from neo4j import Driver

from app.core.config import Settings
from app.domain.entities.character import Character
from app.repositories.interfaces.character_repository import CharacterRepository
from app.repositories.neo4j.base import Neo4jRepositoryBase
from app.repositories.neo4j.mappers import map_character_record


class Neo4jCharacterRepository(Neo4jRepositoryBase, CharacterRepository):
    def __init__(self, driver: Driver, settings: Settings) -> None:
        super().__init__(driver, settings)

    def create(self, character: Character) -> Character:
        query = """
        CREATE (c:Character {
            id: $id,
            slug: $slug,
            name: $name,
            description: $description,
            species: $species,
            homeworld_name: $homeworld_name,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        RETURN properties(c) AS character
        """
        record = self._execute_write("character.create", self._create_tx, query, character)
        return map_character_record(record)

    def get_by_id(self, character_id: str) -> Character | None:
        query = """
        MATCH (c:Character {id: $character_id})
        RETURN properties(c) AS character
        """
        record = self._run_single(query_name="character.get_by_id", query=query, character_id=character_id)
        if record is None:
            return None
        return map_character_record(dict(record["character"]))

    def get_by_slug(self, slug: str) -> Character | None:
        query = """
        MATCH (c:Character {slug: $slug})
        RETURN properties(c) AS character
        """
        record = self._run_single(query_name="character.get_by_slug", query=query, slug=slug)
        if record is None:
            return None
        return map_character_record(dict(record["character"]))

    def list_characters(self) -> list[Character]:
        query = """
        MATCH (c:Character)
        RETURN properties(c) AS character
        ORDER BY c.name ASC
        """
        result = self._run_result(query_name="character.list", query=query)
        return [map_character_record(dict(record["character"])) for record in result]

    @staticmethod
    def _create_tx(tx: Any, query: str, character: Character) -> dict[str, Any]:
        record = tx.run(
            query,
            id=character.id,
            slug=character.slug,
            name=character.name,
            description=character.description,
            species=character.species,
            homeworld_name=character.homeworld_name,
            created_at=character.created_at.isoformat(),
            updated_at=character.updated_at.isoformat(),
        ).single()
        if record is None:
            raise RuntimeError("Failed to create character")
        return dict(record["character"])
