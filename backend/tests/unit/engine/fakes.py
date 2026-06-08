from app.domain.entities.character import Character
from app.domain.entities.causal_graph import CausalGraph
from app.domain.entities.event import Event
from app.domain.entities.faction import Faction
from app.domain.entities.node_reference import NodeReference
from app.domain.entities.planet import Planet
from app.domain.entities.relationship import Relationship
from app.domain.enums import NodeType
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
        limit: int,
        offset: int,
        order: str,
    ) -> tuple[list[Event], int]:
        events = list(self.events_by_id.values())
        if start_year is not None:
            events = [event for event in events if event.start_year >= start_year]
        if end_year is not None:
            events = [event for event in events if (event.end_year or event.start_year) <= end_year]
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


class FakeCharacterRepository(CharacterRepository):
    def __init__(self) -> None:
        self.characters_by_slug: dict[str, Character] = {}

    def create(self, character: Character) -> Character:
        self.characters_by_slug[character.slug] = character
        return character

    def get_by_slug(self, slug: str) -> Character | None:
        return self.characters_by_slug.get(slug)


class FakePlanetRepository(PlanetRepository):
    def __init__(self) -> None:
        self.planets_by_slug: dict[str, Planet] = {}

    def create(self, planet: Planet) -> Planet:
        self.planets_by_slug[planet.slug] = planet
        return planet

    def get_by_slug(self, slug: str) -> Planet | None:
        return self.planets_by_slug.get(slug)


class FakeFactionRepository(FactionRepository):
    def __init__(self) -> None:
        self.factions_by_slug: dict[str, Faction] = {}

    def create(self, faction: Faction) -> Faction:
        self.factions_by_slug[faction.slug] = faction
        return faction

    def get_by_slug(self, slug: str) -> Faction | None:
        return self.factions_by_slug.get(slug)


class FakeGraphRepository(GraphRepository):
    def __init__(self, nodes: list[NodeReference] | None = None) -> None:
        self.nodes_by_id = {node.id: node for node in (nodes or [])}
        self.relationships: list[Relationship] = []

    def get_node_reference(self, node_id: str) -> NodeReference | None:
        return self.nodes_by_id.get(node_id)

    def create_relationship(self, relationship: Relationship) -> Relationship:
        self.relationships.append(relationship)
        return relationship


def make_node(node_id: str, node_type: NodeType) -> NodeReference:
    return NodeReference(id=node_id, node_type=node_type)
