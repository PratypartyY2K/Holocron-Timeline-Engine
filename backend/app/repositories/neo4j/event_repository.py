from typing import Any

from neo4j import Driver

from app.core.config import Settings
from app.domain.entities.causal_graph import CausalGraph, CausalGraphEdge
from app.domain.entities.event import Event
from app.domain.entities.event_impact import EventImpact
from app.domain.enums import RelationshipType
from app.repositories.interfaces.event_repository import EventRepository
from app.repositories.neo4j.mappers import map_event_record


class Neo4jEventRepository(EventRepository):
    def __init__(self, driver: Driver, settings: Settings) -> None:
        self._driver = driver
        self._database = settings.neo4j_database

    def create(self, event: Event) -> Event:
        query = """
        CREATE (e:Event {
            id: $id,
            slug: $slug,
            title: $title,
            description: $description,
            start_year: $start_year,
            end_year: $end_year,
            era: $era,
            canon_status: $canon_status,
            source_refs: $source_refs,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        RETURN properties(e) AS event
        """
        with self._driver.session(database=self._database) as session:
            record = session.execute_write(self._create_tx, query, event)
        return map_event_record(record)

    def get_by_id(self, event_id: str) -> Event | None:
        query = """
        MATCH (e:Event {id: $event_id})
        RETURN properties(e) AS event
        """
        return self._get_one(query, {"event_id": event_id})

    def get_by_slug(self, slug: str) -> Event | None:
        query = """
        MATCH (e:Event {slug: $slug})
        RETURN properties(e) AS event
        """
        return self._get_one(query, {"slug": slug})

    def list_events(
        self,
        *,
        start_year: int | None,
        end_year: int | None,
        era: str | None,
        character: str | None,
        location: str | None,
        causal_depth: int | None,
        limit: int,
        offset: int,
        order: str,
    ) -> tuple[list[Event], int]:
        direction = "ASC" if order == "asc" else "DESC"
        semantic_filter = self._build_semantic_filter(character=character, location=location, causal_depth=causal_depth)
        query = f"""
        MATCH (e:Event)
        WHERE ($start_year IS NULL OR e.start_year >= $start_year)
          AND ($end_year IS NULL OR coalesce(e.end_year, e.start_year) <= $end_year)
          AND ($era IS NULL OR e.era = $era)
          AND {semantic_filter}
        WITH e
        ORDER BY e.start_year {direction}, e.title ASC
        SKIP $offset
        LIMIT $limit
        RETURN collect(properties(e)) AS events
        """
        count_query = f"""
        MATCH (e:Event)
        WHERE ($start_year IS NULL OR e.start_year >= $start_year)
          AND ($end_year IS NULL OR coalesce(e.end_year, e.start_year) <= $end_year)
          AND ($era IS NULL OR e.era = $era)
          AND {semantic_filter}
        RETURN count(e) AS total
        """
        params = {
            "start_year": start_year,
            "end_year": end_year,
            "era": era,
            "character": character,
            "location": location,
            "limit": limit,
            "offset": offset,
        }
        with self._driver.session(database=self._database) as session:
            events_record = session.run(query, **params).single()
            count_record = session.run(count_query, **params).single()
        if events_record is None or count_record is None:
            return [], 0
        event_items = [map_event_record(item) for item in events_record["events"]]
        return event_items, int(count_record["total"])

    def list_dependencies(self, event_id: str, depth: int | None = None) -> list[Event]:
        relationship_pattern = self._causes_path_pattern(depth)
        query = f"""
        MATCH (source:Event)-[:CAUSES{relationship_pattern}]->(target:Event {{id: $event_id}})
        RETURN DISTINCT properties(source) AS event
        ORDER BY event.start_year ASC, event.title ASC
        """
        return self._list_events(query, {"event_id": event_id})

    def list_consequences(self, event_id: str, depth: int | None = None) -> list[Event]:
        relationship_pattern = self._causes_path_pattern(depth)
        query = f"""
        MATCH (source:Event {{id: $event_id}})-[:CAUSES{relationship_pattern}]->(target:Event)
        RETURN DISTINCT properties(target) AS event
        ORDER BY event.start_year ASC, event.title ASC
        """
        return self._list_events(query, {"event_id": event_id})

    def get_causal_graph(self, event_id: str, depth: int) -> CausalGraph:
        edge_query = """
        MATCH (focus:Event {id: $event_id})
        CALL {
            WITH focus
            OPTIONAL MATCH upstream_path = (:Event)-[:CAUSES*1..8]->(focus)
            WHERE length(upstream_path) <= $depth
            UNWIND CASE
                WHEN upstream_path IS NULL THEN []
                ELSE relationships(upstream_path)
            END AS rel
            RETURN collect(DISTINCT rel) AS upstream_rels
        }
        CALL {
            WITH focus
            OPTIONAL MATCH downstream_path = (focus)-[:CAUSES*1..8]->(:Event)
            WHERE length(downstream_path) <= $depth
            UNWIND CASE
                WHEN downstream_path IS NULL THEN []
                ELSE relationships(downstream_path)
            END AS rel
            RETURN collect(DISTINCT rel) AS downstream_rels
        }
        RETURN
            [rel IN [edge IN (upstream_rels + downstream_rels) WHERE edge IS NOT NULL] | {
                id: coalesce(rel.id, startNode(rel).id + '->' + endNode(rel).id),
                source_id: startNode(rel).id,
                target_id: endNode(rel).id,
                type: coalesce(rel.type, 'CAUSES'),
                note: rel.note
            }] AS edges
        """
        node_query = """
        MATCH (e:Event)
        WHERE e.id IN $node_ids
        RETURN properties(e) AS event
        """
        with self._driver.session(database=self._database) as session:
            edge_record = session.run(edge_query, event_id=event_id, depth=depth).single()
            raw_edges = [] if edge_record is None else list(edge_record["edges"])

            node_ids = {event_id}
            for edge in raw_edges:
                node_ids.add(edge["source_id"])
                node_ids.add(edge["target_id"])

            node_result = session.run(node_query, node_ids=list(node_ids))
            nodes = [map_event_record(dict(record["event"])) for record in node_result]

        edges = [
            CausalGraphEdge(
                id=edge["id"],
                source_id=edge["source_id"],
                target_id=edge["target_id"],
                type=RelationshipType(edge["type"]),
                note=edge.get("note"),
            )
            for edge in raw_edges
        ]
        nodes.sort(key=lambda item: (item.start_year, item.title))
        edges.sort(key=lambda item: (item.source_id, item.target_id, item.id))
        return CausalGraph(
            focus_event_id=event_id,
            depth=depth,
            nodes=nodes,
            edges=edges,
        )

    def get_impact(self, event_id: str) -> EventImpact:
        edge_query = """
        MATCH (focus:Event {id: $event_id})
        OPTIONAL MATCH downstream_path = (focus)-[:CAUSES*1..]->(:Event)
        UNWIND CASE
            WHEN downstream_path IS NULL THEN []
            ELSE relationships(downstream_path)
        END AS rel
        RETURN
            [edge IN collect(DISTINCT rel) WHERE edge IS NOT NULL | {
                id: coalesce(edge.id, startNode(edge).id + '->' + endNode(edge).id),
                source_id: startNode(edge).id,
                target_id: endNode(edge).id,
                type: coalesce(edge.type, 'CAUSES'),
                note: edge.note
            }] AS edges
        """
        node_query = """
        MATCH (e:Event)
        WHERE e.id IN $node_ids
        RETURN properties(e) AS event
        """
        with self._driver.session(database=self._database) as session:
            edge_record = session.run(edge_query, event_id=event_id).single()
            raw_edges = [] if edge_record is None else list(edge_record["edges"])

            impacted_node_ids: set[str] = set()
            for edge in raw_edges:
                if edge["source_id"] != event_id:
                    impacted_node_ids.add(edge["source_id"])
                if edge["target_id"] != event_id:
                    impacted_node_ids.add(edge["target_id"])

            node_result = session.run(node_query, node_ids=list(impacted_node_ids))
            impacted_events = [map_event_record(dict(record["event"])) for record in node_result]

        broken_edges = [
            CausalGraphEdge(
                id=edge["id"],
                source_id=edge["source_id"],
                target_id=edge["target_id"],
                type=RelationshipType(edge["type"]),
                note=edge.get("note"),
            )
            for edge in raw_edges
        ]
        impacted_events.sort(key=lambda item: (item.start_year, item.title))
        broken_edges.sort(key=lambda item: (item.source_id, item.target_id, item.id))
        return EventImpact(
            event_id=event_id,
            impacted_events=impacted_events,
            broken_edges=broken_edges,
        )

    @staticmethod
    def _create_tx(tx: Any, query: str, event: Event) -> dict[str, Any]:
        record = tx.run(
            query,
            id=event.id,
            slug=event.slug,
            title=event.title,
            description=event.description,
            start_year=event.start_year,
            end_year=event.end_year,
            era=event.era,
            canon_status=event.canon_status,
            source_refs=event.source_refs,
            created_at=event.created_at.isoformat(),
            updated_at=event.updated_at.isoformat(),
        ).single()
        if record is None:
            raise RuntimeError("Failed to create event")
        return dict(record["event"])

    def _get_one(self, query: str, params: dict[str, Any]) -> Event | None:
        with self._driver.session(database=self._database) as session:
            record = session.run(query, **params).single()
        if record is None:
            return None
        return map_event_record(dict(record["event"]))

    def _list_events(self, query: str, params: dict[str, Any]) -> list[Event]:
        with self._driver.session(database=self._database) as session:
            result = session.run(query, **params)
            return [map_event_record(dict(record["event"])) for record in result]

    @staticmethod
    def _causes_path_pattern(depth: int | None) -> str:
        if depth is None:
            return "*1.."
        return f"*1..{depth}"

    @staticmethod
    def _build_semantic_filter(*, character: str | None, location: str | None, causal_depth: int | None) -> str:
        direct_conditions: list[str] = []
        if character is not None:
            direct_conditions.append(
                "EXISTS { MATCH (e)-[:INVOLVES]->(:Character {slug: $character}) }"
            )
        if location is not None:
            direct_conditions.append(
                "EXISTS { MATCH (e)-[:LOCATED_IN]->(:Planet {slug: $location}) }"
            )

        if not direct_conditions:
            return "true"

        direct_filter = " AND ".join(direct_conditions)
        if causal_depth is None:
            return f"({direct_filter})"

        seed_conditions: list[str] = []
        if character is not None:
            seed_conditions.append(
                "EXISTS { MATCH (seed)-[:INVOLVES]->(:Character {slug: $character}) }"
            )
        if location is not None:
            seed_conditions.append(
                "EXISTS { MATCH (seed)-[:LOCATED_IN]->(:Planet {slug: $location}) }"
            )
        seed_filter = " AND ".join(seed_conditions)
        return (
            "EXISTS { "
            "MATCH (seed:Event) "
            f"WHERE {seed_filter} "
            f"AND EXISTS {{ MATCH (seed)-[:CAUSES*0..{causal_depth}]-(e) }} "
            "}"
        )
