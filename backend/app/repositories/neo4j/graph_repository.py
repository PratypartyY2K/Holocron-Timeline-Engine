from typing import Any

from neo4j import Driver

from app.core.config import Settings
from app.domain.entities.node_reference import NodeReference
from app.domain.entities.relationship import Relationship
from app.repositories.interfaces.graph_repository import GraphRepository
from app.repositories.neo4j.mappers import map_node_reference, map_relationship_record


class Neo4jGraphRepository(GraphRepository):
    def __init__(self, driver: Driver, settings: Settings) -> None:
        self._driver = driver
        self._database = settings.neo4j_database

    def get_node_reference(self, node_id: str) -> NodeReference | None:
        query = """
        MATCH (n {id: $node_id})
        RETURN n.id AS id, labels(n) AS labels
        """
        with self._driver.session(database=self._database) as session:
            record = session.run(query, node_id=node_id).single()
        if record is None:
            return None
        return map_node_reference({"id": record["id"], "labels": list(record["labels"])})

    def get_relationship(
        self,
        *,
        relationship_type: str,
        from_node_id: str,
        to_node_id: str,
    ) -> Relationship | None:
        query = f"""
        MATCH (source {{id: $from_node_id}})-[r:{relationship_type} {{from_node_id: $from_node_id, to_node_id: $to_node_id}}]->(target {{id: $to_node_id}})
        RETURN properties(r) AS relationship
        """
        with self._driver.session(database=self._database) as session:
            record = session.run(query, from_node_id=from_node_id, to_node_id=to_node_id).single()
        if record is None:
            return None
        return map_relationship_record(dict(record["relationship"]))

    def causes_path_exists(self, *, from_node_id: str, to_node_id: str) -> bool:
        query = """
        MATCH (:Event {id: $from_node_id})-[:CAUSES*1..]->(:Event {id: $to_node_id})
        RETURN count(*) > 0 AS path_exists
        """
        with self._driver.session(database=self._database) as session:
            record = session.run(query, from_node_id=from_node_id, to_node_id=to_node_id).single()
        if record is None:
            return False
        return bool(record["path_exists"])

    def get_event_chronology(self, event_id: str) -> tuple[int, int | None] | None:
        query = """
        MATCH (e:Event {id: $event_id})
        RETURN e.start_year AS start_year, e.end_year AS end_year
        """
        with self._driver.session(database=self._database) as session:
            record = session.run(query, event_id=event_id).single()
        if record is None:
            return None
        return int(record["start_year"]), record["end_year"]

    def create_relationship(self, relationship: Relationship) -> Relationship:
        query = f"""
        MATCH (source {{id: $from_node_id}})
        MATCH (target {{id: $to_node_id}})
        CREATE (source)-[r:{relationship.type.value} {{
            id: $id,
            type: $type,
            from_node_id: $from_node_id,
            to_node_id: $to_node_id,
            note: $note,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        }}]->(target)
        RETURN properties(r) AS relationship
        """
        with self._driver.session(database=self._database) as session:
            record = session.execute_write(self._create_tx, query, relationship)
        return map_relationship_record(record)

    @staticmethod
    def _create_tx(tx: Any, query: str, relationship: Relationship) -> dict[str, Any]:
        record = tx.run(
            query,
            id=relationship.id,
            type=relationship.type.value,
            from_node_id=relationship.from_node_id,
            to_node_id=relationship.to_node_id,
            note=relationship.note,
            created_at=relationship.created_at.isoformat(),
            updated_at=relationship.updated_at.isoformat(),
        ).single()
        if record is None:
            raise RuntimeError("Failed to create relationship")
        return dict(record["relationship"])
