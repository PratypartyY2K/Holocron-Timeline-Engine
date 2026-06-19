from app.domain.entities.character import Character
from app.domain.entities.causal_graph import CausalGraph
from app.domain.entities.event import Event
from app.domain.entities.event_impact import EventImpact
from app.domain.entities.faction import Faction
from app.domain.entities.node_reference import NodeReference
from app.domain.entities.planet import Planet
from app.domain.entities.relationship import Relationship
from app.domain.entities.search_result import SearchResult
from app.domain.entities.timeline_break_simulation import TimelineBreakSimulationGraph
from app.domain.enums import NodeType, RelationshipType
from app.repositories.interfaces.character_repository import CharacterRepository
from app.repositories.interfaces.event_repository import EventRepository
from app.repositories.interfaces.faction_repository import FactionRepository
from app.repositories.interfaces.graph_repository import GraphRepository
from app.repositories.interfaces.planet_repository import PlanetRepository


class FakeEventRepository(EventRepository):
    def __init__(self) -> None:
        self.events_by_id: dict[str, Event] = {}
        self.events_by_slug: dict[str, Event] = {}
        self.dependencies: dict[str, list[Event]] = {}
        self.consequences: dict[str, list[Event]] = {}
        self.causal_graphs: dict[tuple[str, int], CausalGraph] = {}
        self.impacts: dict[str, EventImpact] = {}
        self.break_simulation_graphs: dict[str, TimelineBreakSimulationGraph] = {}
        self.last_dependencies_depth: int | None = None
        self.last_consequences_depth: int | None = None
        self.last_causal_graph_depth: int | None = None

    def create(self, event: Event) -> Event:
        self.events_by_id[event.id] = event
        self.events_by_slug[event.slug] = event
        return event

    def get_by_id(self, event_id: str) -> Event | None:
        return self.events_by_id.get(event_id)

    def get_by_slug(self, slug: str) -> Event | None:
        return self.events_by_slug.get(slug)

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
        events = list(self.events_by_id.values())
        if start_year is not None:
            events = [event for event in events if event.start_year >= start_year]
        if end_year is not None:
            events = [event for event in events if (event.end_year or event.start_year) <= end_year]
        if era is not None:
            events = [event for event in events if event.era == era]
        reverse = order == "desc"
        events.sort(key=lambda item: (item.start_year, item.title), reverse=reverse)
        total = len(events)
        return events[offset : offset + limit], total

    def list_dependencies(self, event_id: str, depth: int | None = None) -> list[Event]:
        self.last_dependencies_depth = depth
        return self.dependencies.get(event_id, [])

    def list_consequences(self, event_id: str, depth: int | None = None) -> list[Event]:
        self.last_consequences_depth = depth
        return self.consequences.get(event_id, [])

    def get_causal_graph(self, event_id: str, depth: int) -> CausalGraph:
        self.last_causal_graph_depth = depth
        return self.causal_graphs.get(
            (event_id, depth),
            CausalGraph(focus_event_id=event_id, depth=depth),
        )

    def get_impact(self, event_id: str) -> EventImpact:
        return self.impacts.get(event_id, EventImpact(event_id=event_id))

    def get_break_simulation_graph(self, event_id: str) -> TimelineBreakSimulationGraph:
        return self.break_simulation_graphs.get(event_id, TimelineBreakSimulationGraph(broken_event_id=event_id))


class FakeCharacterRepository(CharacterRepository):
    def __init__(self) -> None:
        self.characters_by_id: dict[str, Character] = {}
        self.characters_by_slug: dict[str, Character] = {}

    def create(self, character: Character) -> Character:
        self.characters_by_id[character.id] = character
        self.characters_by_slug[character.slug] = character
        return character

    def get_by_id(self, character_id: str) -> Character | None:
        return self.characters_by_id.get(character_id)

    def get_by_slug(self, slug: str) -> Character | None:
        return self.characters_by_slug.get(slug)

    def list_characters(self) -> list[Character]:
        return sorted(self.characters_by_slug.values(), key=lambda character: character.name)


class FakePlanetRepository(PlanetRepository):
    def __init__(self) -> None:
        self.planets_by_slug: dict[str, Planet] = {}

    def create(self, planet: Planet) -> Planet:
        self.planets_by_slug[planet.slug] = planet
        return planet

    def get_by_slug(self, slug: str) -> Planet | None:
        return self.planets_by_slug.get(slug)

    def list_planets(self) -> list[Planet]:
        return sorted(self.planets_by_slug.values(), key=lambda planet: planet.name)


class FakeFactionRepository(FactionRepository):
    def __init__(self) -> None:
        self.factions_by_slug: dict[str, Faction] = {}

    def create(self, faction: Faction) -> Faction:
        self.factions_by_slug[faction.slug] = faction
        return faction

    def get_by_slug(self, slug: str) -> Faction | None:
        return self.factions_by_slug.get(slug)

    def list_factions(self) -> list[Faction]:
        return sorted(self.factions_by_slug.values(), key=lambda faction: faction.name)


class FakeGraphRepository(GraphRepository):
    def __init__(self, nodes: list[NodeReference] | None = None) -> None:
        self.nodes_by_id = {node.id: node for node in (nodes or [])}
        self.relationships: list[Relationship] = []
        self.event_chronology_by_id: dict[str, tuple[int, int | None]] = {}
        self.search_results: list[SearchResult] = []
        self.list_state_mutations_before_event_calls: list[str] = []

    def get_node_reference(self, node_id: str) -> NodeReference | None:
        return self.nodes_by_id.get(node_id)

    def get_relationship(
        self,
        *,
        relationship_type: str,
        from_node_id: str,
        to_node_id: str,
        subject_node_id: str | None = None,
        artifact_key: str | None = None,
    ) -> Relationship | None:
        for relationship in self.relationships:
            if (
                relationship.type.value == relationship_type
                and relationship.from_node_id == from_node_id
                and relationship.to_node_id == to_node_id
                and relationship.subject_node_id == subject_node_id
                and relationship.artifact_key == artifact_key
            ):
                return relationship
        return None

    def causes_path_exists(self, *, from_node_id: str, to_node_id: str) -> bool:
        frontier = [from_node_id]
        visited: set[str] = set()
        while frontier:
            current = frontier.pop()
            if current == to_node_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            for relationship in self.relationships:
                if relationship.type is not RelationshipType.CAUSES:
                    continue
                if relationship.from_node_id == current:
                    frontier.append(relationship.to_node_id)
        return False

    def get_event_chronology(self, event_id: str) -> tuple[int, int | None] | None:
        return self.event_chronology_by_id.get(event_id)

    def search_entities(self, *, query: str, limit: int) -> list[SearchResult]:
        normalized_query = query.casefold()
        matches = [
            item
            for item in self.search_results
            if normalized_query in item.label.casefold()
            or normalized_query in item.slug.casefold()
            or normalized_query in (item.description or "").casefold()
        ]
        matches.sort(key=lambda item: (item.label.casefold(), item.entity_type, item.slug.casefold()))
        return matches[:limit]

    def create_relationship(self, relationship: Relationship) -> Relationship:
        self.relationships.append(relationship)
        return relationship

    def list_state_mutations_before_event(self, *, event_id: str) -> list[Relationship]:
        self.list_state_mutations_before_event_calls.append(event_id)
        chronology = self.event_chronology_by_id.get(event_id)
        if chronology is None:
            return []
        focus_start_year = chronology[0]
        event_keys: dict[str, tuple[int, str]] = {}
        for node_id, (start_year, _) in self.event_chronology_by_id.items():
            event_keys[node_id] = (start_year, node_id)
        items = [
            relationship
            for relationship in self.relationships
            if relationship.type
            in {
                RelationshipType.SETS_ALIVE_STATE,
                RelationshipType.SETS_CHARACTER_LOCATION,
                RelationshipType.SETS_PLANET_CONTROL,
                RelationshipType.SETS_ARTIFACT_LOCATION,
            }
            and relationship.from_node_id in event_keys
            and event_keys[relationship.from_node_id][0] < focus_start_year
        ]
        items.sort(key=lambda item: (event_keys[item.from_node_id][0], item.from_node_id, item.id))
        return items


def make_node(node_id: str, node_type: NodeType) -> NodeReference:
    return NodeReference(id=node_id, node_type=node_type)
