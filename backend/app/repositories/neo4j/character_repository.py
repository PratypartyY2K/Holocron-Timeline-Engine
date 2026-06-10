from typing import Any

from neo4j import Driver

from app.core.config import Settings
from app.domain.entities.character import Character
from app.repositories.interfaces.character_repository import CharacterRepository
from app.repositories.neo4j.mappers import map_character_record


class Neo4jCharacterRepository(CharacterRepository):
    def __init__(self, driver: Driver, settings: Settings) -> None:
        self._driver = driver
        self._database = settings.neo4j_database

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
        with self._driver.session(database=self._database) as session:
            record = session.execute_write(self._create_tx, query, character)
        return map_character_record(record)

    def get_by_slug(self, slug: str) -> Character | None:
        query = """
        MATCH (c:Character {slug: $slug})
        RETURN properties(c) AS character
        """
        with self._driver.session(database=self._database) as session:
            record = session.run(query, slug=slug).single()
        if record is None:
            return None
        return map_character_record(dict(record["character"]))

    def list_characters(self) -> list[Character]:
        query = """
        MATCH (c:Character)
        RETURN properties(c) AS character
        ORDER BY c.name ASC
        """
        with self._driver.session(database=self._database) as session:
            result = session.run(query)
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
