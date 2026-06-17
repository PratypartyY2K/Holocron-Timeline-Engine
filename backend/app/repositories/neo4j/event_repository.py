from typing import Any

from neo4j import Driver

from app.core.config import Settings
from app.domain.entities.causal_graph import CausalGraph, CausalGraphEdge
from app.domain.entities.event import Event
from app.domain.entities.event_impact import EventImpact
from app.domain.entities.timeline_break_simulation import TimelineBreakSimulationGraph
from app.domain.enums import RelationshipType
from app.repositories.interfaces.event_repository import EventRepository
from app.repositories.neo4j.base import Neo4jRepositoryBase
from app.repositories.neo4j.mappers import map_event_record


class Neo4jEventRepository(Neo4jRepositoryBase, EventRepository):
    def __init__(self, driver: Driver, settings: Settings) -> None:
        super().__init__(driver, settings)

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
        record = self._execute_write("event.create", self._create_tx, query, event)
        return map_event_record(record)

    def get_by_id(self, event_id: str) -> Event | None:
        query = """
        MATCH (e:Event {id: $event_id})
        CALL {
            WITH e
            OPTIONAL MATCH (dependency:Event)-[:CAUSES*1..]->(e)
            RETURN count(DISTINCT dependency) AS dependency_count
        }
        CALL {
            WITH e
            OPTIONAL MATCH (incoming:Event)-[:CAUSES]->(e)
            RETURN count(DISTINCT incoming) AS incoming_degree
        }
        CALL {
            WITH e
            OPTIONAL MATCH (e)-[:CAUSES]->(outgoing:Event)
            RETURN count(DISTINCT outgoing) AS outgoing_degree
        }
        CALL {
            WITH e
            OPTIONAL MATCH (e)-[:INVOLVES]->(faction:Faction)
            RETURN
                collect(DISTINCT faction.slug) AS faction_slugs,
                collect(DISTINCT faction.name) AS faction_names
        }
        CALL {
            MATCH (all_events:Event)
            RETURN count(all_events) AS total_events
        }
        RETURN e {
            .*,
            dependency_count: dependency_count,
            centrality_score: CASE
                WHEN total_events <= 1 THEN 0.0
                ELSE toFloat(incoming_degree + outgoing_degree) / toFloat(2 * (total_events - 1))
            END,
            faction_slugs: faction_slugs,
            faction_names: faction_names
        } AS event
        """
        return self._get_one(query, {"event_id": event_id})

    def get_by_slug(self, slug: str) -> Event | None:
        query = """
        MATCH (e:Event {slug: $slug})
        CALL {
            WITH e
            OPTIONAL MATCH (dependency:Event)-[:CAUSES*1..]->(e)
            RETURN count(DISTINCT dependency) AS dependency_count
        }
        CALL {
            WITH e
            OPTIONAL MATCH (incoming:Event)-[:CAUSES]->(e)
            RETURN count(DISTINCT incoming) AS incoming_degree
        }
        CALL {
            WITH e
            OPTIONAL MATCH (e)-[:CAUSES]->(outgoing:Event)
            RETURN count(DISTINCT outgoing) AS outgoing_degree
        }
        CALL {
            WITH e
            OPTIONAL MATCH (e)-[:INVOLVES]->(faction:Faction)
            RETURN
                collect(DISTINCT faction.slug) AS faction_slugs,
                collect(DISTINCT faction.name) AS faction_names
        }
        CALL {
            MATCH (all_events:Event)
            RETURN count(all_events) AS total_events
        }
        RETURN e {
            .*,
            dependency_count: dependency_count,
            centrality_score: CASE
                WHEN total_events <= 1 THEN 0.0
                ELSE toFloat(incoming_degree + outgoing_degree) / toFloat(2 * (total_events - 1))
            END,
            faction_slugs: faction_slugs,
            faction_names: faction_names
        } AS event
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
        CALL {{
            WITH e
            OPTIONAL MATCH (dependency:Event)-[:CAUSES*1..]->(e)
            RETURN count(DISTINCT dependency) AS dependency_count
        }}
        CALL {{
            WITH e
            OPTIONAL MATCH (incoming:Event)-[:CAUSES]->(e)
            RETURN count(DISTINCT incoming) AS incoming_degree
        }}
        CALL {{
            WITH e
            OPTIONAL MATCH (e)-[:CAUSES]->(outgoing:Event)
            RETURN count(DISTINCT outgoing) AS outgoing_degree
        }}
        CALL {{
            WITH e
            OPTIONAL MATCH (e)-[:INVOLVES]->(faction:Faction)
            RETURN
                collect(DISTINCT faction.slug) AS faction_slugs,
                collect(DISTINCT faction.name) AS faction_names
        }}
        CALL {{
            MATCH (all_events:Event)
            RETURN count(all_events) AS total_events
        }}
        RETURN e {{
            .*,
            dependency_count: dependency_count,
            centrality_score: CASE
                WHEN total_events <= 1 THEN 0.0
                ELSE toFloat(incoming_degree + outgoing_degree) / toFloat(2 * (total_events - 1))
            END,
            faction_slugs: faction_slugs,
            faction_names: faction_names
        }} AS event
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
        def operation() -> tuple[list[Any], Any]:
            with self._driver.session(database=self._database) as session:
                event_records = list(session.run(query, **params))
                count_record = session.run(count_query, **params).single()
                return event_records, count_record

        event_records, count_record = self._measure_query("event.list", operation)
        if count_record is None:
            return [], 0
        event_items = [map_event_record(dict(record["event"])) for record in event_records]
        return event_items, int(count_record["total"])

    def list_dependencies(self, event_id: str, depth: int | None = None) -> list[Event]:
        relationship_pattern = self._causes_path_pattern(depth)
        query = f"""
        MATCH (source:Event)-[:CAUSES{relationship_pattern}]->(target:Event {{id: $event_id}})
        WITH DISTINCT source
        CALL {{
            WITH source
            OPTIONAL MATCH (dependency:Event)-[:CAUSES*1..]->(source)
            RETURN count(DISTINCT dependency) AS dependency_count
        }}
        CALL {{
            WITH source
            OPTIONAL MATCH (incoming:Event)-[:CAUSES]->(source)
            RETURN count(DISTINCT incoming) AS incoming_degree
        }}
        CALL {{
            WITH source
            OPTIONAL MATCH (source)-[:CAUSES]->(outgoing:Event)
            RETURN count(DISTINCT outgoing) AS outgoing_degree
        }}
        CALL {{
            WITH source
            OPTIONAL MATCH (source)-[:INVOLVES]->(faction:Faction)
            RETURN
                collect(DISTINCT faction.slug) AS faction_slugs,
                collect(DISTINCT faction.name) AS faction_names
        }}
        CALL {{
            MATCH (all_events:Event)
            RETURN count(all_events) AS total_events
        }}
        RETURN DISTINCT source {{
            .*,
            dependency_count: dependency_count,
            centrality_score: CASE
                WHEN total_events <= 1 THEN 0.0
                ELSE toFloat(incoming_degree + outgoing_degree) / toFloat(2 * (total_events - 1))
            END,
            faction_slugs: faction_slugs,
            faction_names: faction_names
        }} AS event
        ORDER BY event.start_year ASC, event.title ASC
        """
        return self._list_events(query, {"event_id": event_id})

    def list_consequences(self, event_id: str, depth: int | None = None) -> list[Event]:
        relationship_pattern = self._causes_path_pattern(depth)
        query = f"""
        MATCH (source:Event {{id: $event_id}})-[:CAUSES{relationship_pattern}]->(target:Event)
        WITH DISTINCT target
        CALL {{
            WITH target
            OPTIONAL MATCH (dependency:Event)-[:CAUSES*1..]->(target)
            RETURN count(DISTINCT dependency) AS dependency_count
        }}
        CALL {{
            WITH target
            OPTIONAL MATCH (incoming:Event)-[:CAUSES]->(target)
            RETURN count(DISTINCT incoming) AS incoming_degree
        }}
        CALL {{
            WITH target
            OPTIONAL MATCH (target)-[:CAUSES]->(outgoing:Event)
            RETURN count(DISTINCT outgoing) AS outgoing_degree
        }}
        CALL {{
            WITH target
            OPTIONAL MATCH (target)-[:INVOLVES]->(faction:Faction)
            RETURN
                collect(DISTINCT faction.slug) AS faction_slugs,
                collect(DISTINCT faction.name) AS faction_names
        }}
        CALL {{
            MATCH (all_events:Event)
            RETURN count(all_events) AS total_events
        }}
        RETURN DISTINCT target {{
            .*,
            dependency_count: dependency_count,
            centrality_score: CASE
                WHEN total_events <= 1 THEN 0.0
                ELSE toFloat(incoming_degree + outgoing_degree) / toFloat(2 * (total_events - 1))
            END,
            faction_slugs: faction_slugs,
            faction_names: faction_names
        }} AS event
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
        CALL {
            WITH e
            OPTIONAL MATCH (dependency:Event)-[:CAUSES*1..]->(e)
            RETURN count(DISTINCT dependency) AS dependency_count
        }
        CALL {
            WITH e
            OPTIONAL MATCH (incoming:Event)-[:CAUSES]->(e)
            RETURN count(DISTINCT incoming) AS incoming_degree
        }
        CALL {
            WITH e
            OPTIONAL MATCH (e)-[:CAUSES]->(outgoing:Event)
            RETURN count(DISTINCT outgoing) AS outgoing_degree
        }
        CALL {
            WITH e
            OPTIONAL MATCH (e)-[:INVOLVES]->(faction:Faction)
            RETURN
                collect(DISTINCT faction.slug) AS faction_slugs,
                collect(DISTINCT faction.name) AS faction_names
        }
        CALL {
            MATCH (all_events:Event)
            RETURN count(all_events) AS total_events
        }
        RETURN e {
            .*,
            dependency_count: dependency_count,
            centrality_score: CASE
                WHEN total_events <= 1 THEN 0.0
                ELSE toFloat(incoming_degree + outgoing_degree) / toFloat(2 * (total_events - 1))
            END,
            faction_slugs: faction_slugs,
            faction_names: faction_names
        } AS event
        """
        def operation() -> tuple[list[dict[str, Any]], list[Event]]:
            with self._driver.session(database=self._database) as session:
                edge_record = session.run(edge_query, event_id=event_id, depth=depth).single()
                raw_edges = [] if edge_record is None else list(edge_record["edges"])

                node_ids = {event_id}
                for edge in raw_edges:
                    node_ids.add(edge["source_id"])
                    node_ids.add(edge["target_id"])

                node_result = session.run(node_query, node_ids=list(node_ids))
                nodes = [map_event_record(dict(record["event"])) for record in node_result]
                return raw_edges, nodes

        raw_edges, nodes = self._measure_query("event.get_causal_graph", operation)

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
        CALL {
            WITH e
            OPTIONAL MATCH (dependency:Event)-[:CAUSES*1..]->(e)
            RETURN count(DISTINCT dependency) AS dependency_count
        }
        CALL {
            WITH e
            OPTIONAL MATCH (incoming:Event)-[:CAUSES]->(e)
            RETURN count(DISTINCT incoming) AS incoming_degree
        }
        CALL {
            WITH e
            OPTIONAL MATCH (e)-[:CAUSES]->(outgoing:Event)
            RETURN count(DISTINCT outgoing) AS outgoing_degree
        }
        CALL {
            WITH e
            OPTIONAL MATCH (e)-[:INVOLVES]->(faction:Faction)
            RETURN
                collect(DISTINCT faction.slug) AS faction_slugs,
                collect(DISTINCT faction.name) AS faction_names
        }
        CALL {
            MATCH (all_events:Event)
            RETURN count(all_events) AS total_events
        }
        RETURN e {
            .*,
            dependency_count: dependency_count,
            centrality_score: CASE
                WHEN total_events <= 1 THEN 0.0
                ELSE toFloat(incoming_degree + outgoing_degree) / toFloat(2 * (total_events - 1))
            END,
            faction_slugs: faction_slugs,
            faction_names: faction_names
        } AS event
        """
        def operation() -> tuple[list[dict[str, Any]], list[Event]]:
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
                return raw_edges, impacted_events

        raw_edges, impacted_events = self._measure_query("event.get_impact", operation)

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

    def get_break_simulation_graph(self, event_id: str) -> TimelineBreakSimulationGraph:
        downstream_ids_query = """
        MATCH (:Event {id: $event_id})-[:CAUSES*1..]->(downstream:Event)
        RETURN collect(DISTINCT downstream.id) AS downstream_ids
        """
        node_query = """
        MATCH (e:Event)
        WHERE e.id IN $node_ids
        RETURN properties(e) AS event
        """
        edge_query = """
        MATCH (source:Event)-[rel:CAUSES]->(target:Event)
        WHERE source.id IN $simulation_ids AND target.id IN $simulation_ids
        RETURN {
            id: coalesce(rel.id, source.id + '->' + target.id),
            source_id: source.id,
            target_id: target.id,
            type: coalesce(rel.type, 'CAUSES'),
            note: rel.note
        } AS edge
        """
        dependency_query = """
        MATCH (source:Event)-[:CAUSES]->(target:Event)
        WHERE target.id IN $downstream_ids
        RETURN target.id AS target_id, collect(DISTINCT source.id) AS dependency_source_ids
        """

        def operation() -> tuple[list[Event], list[CausalGraphEdge], dict[str, list[str]]]:
            with self._driver.session(database=self._database) as session:
                downstream_ids_record = session.run(downstream_ids_query, event_id=event_id).single()
                downstream_ids = [] if downstream_ids_record is None else list(downstream_ids_record["downstream_ids"])
                simulation_ids = [event_id, *downstream_ids]

                node_result = session.run(node_query, node_ids=simulation_ids)
                edge_result = session.run(edge_query, simulation_ids=simulation_ids)
                dependency_result = session.run(dependency_query, downstream_ids=downstream_ids)

                downstream_events = [map_event_record(dict(record["event"])) for record in node_result]
                internal_edges = [
                    CausalGraphEdge(
                        id=record["edge"]["id"],
                        source_id=record["edge"]["source_id"],
                        target_id=record["edge"]["target_id"],
                        type=RelationshipType(record["edge"]["type"]),
                        note=record["edge"].get("note"),
                    )
                    for record in edge_result
                ]
                dependency_ids_by_event_id = {
                    record["target_id"]: list(record["dependency_source_ids"])
                    for record in dependency_result
                }
                return downstream_events, internal_edges, dependency_ids_by_event_id

        downstream_events, internal_edges, dependency_ids_by_event_id = self._measure_query(
            "event.get_break_simulation_graph",
            operation,
        )

        downstream_events = [event for event in downstream_events if event.id != event_id]
        downstream_events.sort(key=lambda item: (item.start_year, item.title, item.id))
        internal_edges.sort(key=lambda item: (item.source_id, item.target_id, item.id))
        return TimelineBreakSimulationGraph(
            broken_event_id=event_id,
            downstream_events=downstream_events,
            internal_edges=internal_edges,
            dependency_ids_by_event_id=dependency_ids_by_event_id,
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
        record = self._run_single(query_name="event.get_one", query=query, **params)
        if record is None:
            return None
        return map_event_record(dict(record["event"]))

    def _list_events(self, query: str, params: dict[str, Any]) -> list[Event]:
        result = self._run_result(query_name="event.list_related", query=query, **params)
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
