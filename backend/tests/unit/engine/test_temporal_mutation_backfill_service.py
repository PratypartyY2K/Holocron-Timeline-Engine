from app.domain.entities.character import Character
from app.domain.entities.event import Event
from app.domain.entities.faction import Faction
from app.domain.entities.planet import Planet
from app.domain.enums import NodeType
from app.engine.services.relationship_service import RelationshipService
from app.engine.services.temporal_mutation_backfill_service import TemporalMutationBackfillService
from tests.unit.engine.fakes import (
    FakeCharacterRepository,
    FakeEventRepository,
    FakeFactionRepository,
    FakeGraphRepository,
    FakePlanetRepository,
    make_node,
)


def make_backfill_service() -> tuple[TemporalMutationBackfillService, FakeGraphRepository]:
    event_repository = FakeEventRepository()
    for event in (
        Event(
            "event-rise-empire",
            "rise-of-the-empire",
            "Rise of the Empire",
            None,
            -19,
            -19,
            None,
            None,
        ),
        Event("event-battle-yavin", "battle-of-yavin", "Battle of Yavin", None, 0, 0, None, None),
        Event("event-battle-crait", "battle-of-crait", "Battle of Crait", None, 34, 34, None, None),
        Event(
            "event-battle-exegol", "battle-of-exegol", "Battle of Exegol", None, 35, 35, None, None
        ),
    ):
        event_repository.create(event)

    character_repository = FakeCharacterRepository()
    for character in (
        Character("char-luke", "luke-skywalker", "Luke Skywalker", None, None, None),
        Character("char-tarkin", "grand-moff-tarkin", "Grand Moff Tarkin", None, None, None),
        Character("char-palpatine", "sheev-palpatine", "Sheev Palpatine", None, None, None),
    ):
        character_repository.create(character)

    planet_repository = FakePlanetRepository()
    for planet in (
        Planet("planet-alderaan", "alderaan", "Alderaan", None, None),
        Planet("planet-coruscant", "coruscant", "Coruscant", None, None),
        Planet("planet-naboo", "naboo", "Naboo", None, None),
    ):
        planet_repository.create(planet)

    faction_repository = FakeFactionRepository()
    for faction in (
        Faction("faction-republic", "galactic-republic", "Galactic Republic", None),
        Faction("faction-empire", "galactic-empire", "Galactic Empire", None),
    ):
        faction_repository.create(faction)

    graph_repository = FakeGraphRepository(
        nodes=[
            make_node("event-rise-empire", NodeType.EVENT),
            make_node("event-battle-yavin", NodeType.EVENT),
            make_node("event-battle-crait", NodeType.EVENT),
            make_node("event-battle-exegol", NodeType.EVENT),
            make_node("char-luke", NodeType.CHARACTER),
            make_node("char-tarkin", NodeType.CHARACTER),
            make_node("char-palpatine", NodeType.CHARACTER),
            make_node("planet-alderaan", NodeType.PLANET),
            make_node("planet-coruscant", NodeType.PLANET),
            make_node("planet-naboo", NodeType.PLANET),
            make_node("faction-empire", NodeType.FACTION),
        ]
    )
    graph_repository.event_chronology_by_id = {
        "event-rise-empire": (-19, -19),
        "event-battle-yavin": (0, 0),
        "event-battle-crait": (34, 34),
        "event-battle-exegol": (35, 35),
    }
    relationship_service = RelationshipService(graph_repository)

    return (
        TemporalMutationBackfillService(
            event_repository=event_repository,
            character_repository=character_repository,
            planet_repository=planet_repository,
            faction_repository=faction_repository,
            relationship_service=relationship_service,
        ),
        graph_repository,
    )


def test_backfill_plans_curated_mutations() -> None:
    service, _ = make_backfill_service()

    result = service.backfill(dry_run=True)

    assert result.planned == 6
    assert result.applied == 0
    assert result.skipped_duplicates == 0
    assert result.skipped_missing_entities == ()


def test_backfill_applies_mutations_idempotently() -> None:
    service, graph_repository = make_backfill_service()

    first = service.backfill()
    second = service.backfill()

    assert first.applied == 6
    assert second.skipped_duplicates == 6
    assert len(graph_repository.relationships) == 6


def test_backfill_skips_missing_curated_entities_without_crashing() -> None:
    service, _ = make_backfill_service()
    service._character_repository.characters_by_slug.pop("grand-moff-tarkin")

    result = service.backfill(dry_run=True)

    assert result.planned == 5
    assert any("grand-moff-tarkin" in item for item in result.skipped_missing_entities)


def test_backfill_resolves_tarkin_slug_alias() -> None:
    service, _ = make_backfill_service()
    tarkin = service._character_repository.characters_by_slug.pop("grand-moff-tarkin")
    service._character_repository.characters_by_slug["wilhuff-tarkin"] = tarkin

    result = service.backfill(dry_run=True)

    assert result.planned == 6
    assert result.skipped_missing_entities == ()
