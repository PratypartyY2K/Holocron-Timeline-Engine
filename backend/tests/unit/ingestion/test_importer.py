from app.domain.entities.node_reference import NodeReference
from app.domain.enums import NodeType
from app.engine.services.character_service import CharacterService
from app.engine.services.event_service import EventService
from app.engine.services.faction_service import FactionService
from app.engine.services.planet_service import PlanetService
from app.engine.services.relationship_service import RelationshipService
from app.ingestion.importer import DatasetImporter
from app.ingestion.models import Dataset
from tests.unit.engine.fakes import (
    FakeCharacterRepository,
    FakeEventRepository,
    FakeFactionRepository,
    FakeGraphRepository,
    FakePlanetRepository,
)


class GraphAwareEventRepository(FakeEventRepository):
    def __init__(self, graph_repository: FakeGraphRepository) -> None:
        super().__init__()
        self._graph_repository = graph_repository

    def create(self, event):
        created = super().create(event)
        self._graph_repository.nodes_by_id[created.id] = NodeReference(
            id=created.id, node_type=NodeType.EVENT
        )
        self._graph_repository.event_chronology_by_id[created.id] = (
            created.start_year,
            created.end_year,
        )
        return created


class GraphAwareCharacterRepository(FakeCharacterRepository):
    def __init__(self, graph_repository: FakeGraphRepository) -> None:
        super().__init__()
        self._graph_repository = graph_repository

    def create(self, character):
        created = super().create(character)
        self._graph_repository.nodes_by_id[created.id] = NodeReference(
            id=created.id, node_type=NodeType.CHARACTER
        )
        return created


class GraphAwarePlanetRepository(FakePlanetRepository):
    def __init__(self, graph_repository: FakeGraphRepository) -> None:
        super().__init__()
        self._graph_repository = graph_repository

    def create(self, planet):
        created = super().create(planet)
        self._graph_repository.nodes_by_id[created.id] = NodeReference(
            id=created.id, node_type=NodeType.PLANET
        )
        return created


class GraphAwareFactionRepository(FakeFactionRepository):
    def __init__(self, graph_repository: FakeGraphRepository) -> None:
        super().__init__()
        self._graph_repository = graph_repository

    def create(self, faction):
        created = super().create(faction)
        self._graph_repository.nodes_by_id[created.id] = NodeReference(
            id=created.id, node_type=NodeType.FACTION
        )
        return created


def make_importer() -> tuple[DatasetImporter, FakeGraphRepository]:
    graph_repository = FakeGraphRepository()
    importer = DatasetImporter(
        event_service=EventService(GraphAwareEventRepository(graph_repository)),
        character_service=CharacterService(GraphAwareCharacterRepository(graph_repository)),
        planet_service=PlanetService(GraphAwarePlanetRepository(graph_repository)),
        faction_service=FactionService(GraphAwareFactionRepository(graph_repository)),
        relationship_service=RelationshipService(graph_repository),
    )
    return importer, graph_repository


def test_import_dataset_creates_entities_and_relationships() -> None:
    importer, graph_repository = make_importer()
    dataset = Dataset.model_validate(
        {
            "events": [
                {
                    "slug": "battle-of-yavin",
                    "title": "Battle of Yavin",
                    "start_year": 0,
                    "end_year": 0,
                }
            ],
            "characters": [
                {
                    "slug": "luke-skywalker",
                    "name": "Luke Skywalker",
                }
            ],
            "relationships": [
                {
                    "type": "INVOLVES",
                    "source": {"type": "event", "slug": "battle-of-yavin"},
                    "target": {"type": "character", "slug": "luke-skywalker"},
                    "note": "Primary pilot",
                }
            ],
        }
    )

    result = importer.import_dataset(dataset)

    assert result.events.created == 1
    assert result.characters.created == 1
    assert result.relationships.created == 1
    assert len(graph_repository.relationships) == 1


def test_import_dataset_skips_existing_records_and_duplicate_relationships() -> None:
    importer, _ = make_importer()
    dataset = Dataset.model_validate(
        {
            "factions": [
                {
                    "slug": "galactic-empire",
                    "name": "Galactic Empire",
                },
                {
                    "slug": "rebel-alliance",
                    "name": "Rebel Alliance",
                },
            ],
            "relationships": [
                {
                    "type": "ALLIED_WITH",
                    "source": {"type": "faction", "slug": "rebel-alliance"},
                    "target": {"type": "faction", "slug": "galactic-empire"},
                    "note": "Impossible alliance",
                }
            ],
        }
    )

    first = importer.import_dataset(dataset)
    second = importer.import_dataset(dataset)

    assert first.factions.created == 2
    assert first.relationships.created == 1
    assert second.factions.skipped == 2
    assert second.relationships.skipped == 1
