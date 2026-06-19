from typing import Any

from neo4j import Driver

from app.core.config import Settings
from app.domain.entities.node_reference import NodeReference
from app.domain.entities.relationship import Relationship
from app.domain.entities.search_result import SearchResult
from app.repositories.interfaces.graph_repository import GraphRepository
from app.repositories.neo4j.base import Neo4jRepositoryBase
from app.repositories.neo4j.mappers import map_node_reference, map_relationship_record


class Neo4jGraphRepository(Neo4jRepositoryBase, GraphRepository):
    def __init__(self, driver: Driver, settings: Settings) -> None:
        super().__init__(driver, settings)

    def get_node_reference(self, node_id: str) -> NodeReference | None:
        query = """
        MATCH (n {id: $node_id})
        RETURN n.id AS id, labels(n) AS labels
        """
        record = self._run_single(
            query_name="graph.get_node_reference", query=query, node_id=node_id
        )
        if record is None:
            return None
        return map_node_reference({"id": record["id"], "labels": list(record["labels"])})

    def get_relationship(
        self,
        *,
        relationship_type: str,
        from_node_id: str,
        to_node_id: str,
        subject_node_id: str | None = None,
        artifact_key: str | None = None,
    ) -> Relationship | None:
        query = """
        MATCH (source {id: $from_node_id})-[r]->(target {id: $to_node_id})
        WHERE type(r) = $relationship_type
          AND r.from_node_id = $from_node_id
          AND r.to_node_id = $to_node_id
          AND (($subject_node_id IS NULL AND r[$subject_key] IS NULL) OR r[$subject_key] = $subject_node_id)
          AND (($artifact_key IS NULL AND r[$artifact_key_name] IS NULL) OR r[$artifact_key_name] = $artifact_key)
        RETURN properties(r) AS relationship
        """
        record = self._run_single(
            query_name="graph.get_relationship",
            query=query,
            relationship_type=relationship_type,
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            subject_node_id=subject_node_id,
            artifact_key=artifact_key,
            subject_key="subject_node_id",
            artifact_key_name="artifact_key",
        )
        if record is None:
            return None
        return map_relationship_record(dict(record["relationship"]))

    def causes_path_exists(self, *, from_node_id: str, to_node_id: str) -> bool:
        query = """
        MATCH (:Event {id: $from_node_id})-[:CAUSES*1..]->(:Event {id: $to_node_id})
        RETURN count(*) > 0 AS path_exists
        """
        record = self._run_single(
            query_name="graph.causes_path_exists",
            query=query,
            from_node_id=from_node_id,
            to_node_id=to_node_id,
        )
        if record is None:
            return False
        return bool(record["path_exists"])

    def get_event_chronology(self, event_id: str) -> tuple[int, int | None] | None:
        query = """
        MATCH (e:Event {id: $event_id})
        RETURN e.start_year AS start_year, e.end_year AS end_year
        """
        record = self._run_single(
            query_name="graph.get_event_chronology", query=query, event_id=event_id
        )
        if record is None:
            return None
        return int(record["start_year"]), record["end_year"]

    def search_entities(self, *, query: str, limit: int) -> list[SearchResult]:
        cypher = """
        CALL {
            WITH $normalized_query AS normalized_query
            MATCH (e:Event)
            WITH e,
                CASE
                    WHEN toLower(e.title) = normalized_query OR toLower(e.slug) = normalized_query THEN 0
                    WHEN toLower(e.title) STARTS WITH normalized_query OR toLower(e.slug) STARTS WITH normalized_query THEN 1
                    WHEN toLower(e.title) CONTAINS normalized_query OR toLower(e.slug) CONTAINS normalized_query THEN 2
                    WHEN toLower(coalesce(e.description, '')) CONTAINS normalized_query THEN 3
                    ELSE 99
                END AS score
            WHERE score < 99
            RETURN 'event' AS entity_type, e.id AS id, e.slug AS slug, e.title AS label, e.description AS description, score

            UNION ALL

            WITH $normalized_query AS normalized_query
            MATCH (c:Character)
            WITH c,
                CASE
                    WHEN toLower(c.name) = normalized_query OR toLower(c.slug) = normalized_query THEN 0
                    WHEN toLower(c.name) STARTS WITH normalized_query OR toLower(c.slug) STARTS WITH normalized_query THEN 1
                    WHEN toLower(c.name) CONTAINS normalized_query OR toLower(c.slug) CONTAINS normalized_query THEN 2
                    WHEN toLower(coalesce(c.description, '')) CONTAINS normalized_query
                      OR toLower(coalesce(c.species, '')) CONTAINS normalized_query
                      OR toLower(coalesce(c.homeworld_name, '')) CONTAINS normalized_query THEN 3
                    ELSE 99
                END AS score
            WHERE score < 99
            RETURN 'character' AS entity_type, c.id AS id, c.slug AS slug, c.name AS label, c.description AS description, score

            UNION ALL

            WITH $normalized_query AS normalized_query
            MATCH (p:Planet)
            WITH p,
                CASE
                    WHEN toLower(p.name) = normalized_query OR toLower(p.slug) = normalized_query THEN 0
                    WHEN toLower(p.name) STARTS WITH normalized_query OR toLower(p.slug) STARTS WITH normalized_query THEN 1
                    WHEN toLower(p.name) CONTAINS normalized_query OR toLower(p.slug) CONTAINS normalized_query THEN 2
                    WHEN toLower(coalesce(p.description, '')) CONTAINS normalized_query
                      OR toLower(coalesce(p.region, '')) CONTAINS normalized_query THEN 3
                    ELSE 99
                END AS score
            WHERE score < 99
            RETURN 'planet' AS entity_type, p.id AS id, p.slug AS slug, p.name AS label, p.description AS description, score

            UNION ALL

            WITH $normalized_query AS normalized_query
            MATCH (f:Faction)
            WITH f,
                CASE
                    WHEN toLower(f.name) = normalized_query OR toLower(f.slug) = normalized_query THEN 0
                    WHEN toLower(f.name) STARTS WITH normalized_query OR toLower(f.slug) STARTS WITH normalized_query THEN 1
                    WHEN toLower(f.name) CONTAINS normalized_query OR toLower(f.slug) CONTAINS normalized_query THEN 2
                    WHEN toLower(coalesce(f.description, '')) CONTAINS normalized_query THEN 3
                    ELSE 99
                END AS score
            WHERE score < 99
            RETURN 'faction' AS entity_type, f.id AS id, f.slug AS slug, f.name AS label, f.description AS description, score
        }
        RETURN entity_type, id, slug, label, description
        ORDER BY score ASC, label ASC, entity_type ASC
        LIMIT $limit
        """
        result = self._run_result(
            query_name="graph.search_entities",
            query=cypher,
            normalized_query=query.casefold(),
            limit=limit,
        )
        return [
            SearchResult(
                entity_type=record["entity_type"],
                id=record["id"],
                slug=record["slug"],
                label=record["label"],
                description=record["description"],
            )
            for record in result
        ]

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
            subject_node_id: $subject_node_id,
            artifact_key: $artifact_key,
            value_bool: $value_bool,
            value_text: $value_text,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        }}]->(target)
        RETURN properties(r) AS relationship
        """
        record = self._execute_write(
            "graph.create_relationship", self._create_tx, query, relationship
        )
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
            subject_node_id=relationship.subject_node_id,
            artifact_key=relationship.artifact_key,
            value_bool=relationship.value_bool,
            value_text=relationship.value_text,
            created_at=relationship.created_at.isoformat(),
            updated_at=relationship.updated_at.isoformat(),
        ).single()
        if record is None:
            raise RuntimeError("Failed to create relationship")
        return dict(record["relationship"])

    def list_state_mutations_before_event(self, *, event_id: str) -> list[Relationship]:
        query = """
        MATCH (focus:Event {id: $event_id})
        MATCH (source:Event)-[r]->()
        WHERE (
            source.start_year < focus.start_year
            OR (source.start_year = focus.start_year AND source.title < focus.title)
            OR (source.start_year = focus.start_year AND source.title = focus.title AND source.id < focus.id)
        )
        AND type(r) IN $relationship_types
        RETURN properties(r) AS relationship
        ORDER BY source.start_year ASC, source.title ASC, source.id ASC, r.id ASC
        """
        result = self._run_result(
            query_name="graph.list_state_mutations_before_event",
            query=query,
            event_id=event_id,
            relationship_types=[
                "SETS_ALIVE_STATE",
                "SETS_CHARACTER_LOCATION",
                "SETS_PLANET_CONTROL",
                "SETS_ARTIFACT_LOCATION",
            ],
        )
        return [map_relationship_record(dict(record["relationship"])) for record in result]
