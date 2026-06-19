from app.domain.entities.character import Character
from app.domain.entities.event import Event
from app.domain.entities.faction import Faction
from app.domain.entities.planet import Planet
from app.domain.enums import NodeType, RelationshipType
from app.engine.dto import CreateRelationshipCommand
from app.engine.services.relationship_service import RelationshipService
from app.engine.services.universe_state_service import UniverseStateService
from tests.unit.engine.fakes import (
    FakeCharacterRepository,
    FakeEventRepository,
    FakeFactionRepository,
    FakeGraphRepository,
    FakePlanetRepository,
    make_node,
)


def make_service() -> UniverseStateService:
    UniverseStateService.invalidate_projection_cache()
    event_repository = FakeEventRepository()
    event_repository.create(
        Event(
            id="event-rise-empire",
            slug="rise-of-the-empire",
            title="Rise of the Empire",
            description=None,
            start_year=-19,
            end_year=-19,
            era=None,
            canon_status=None,
        )
    )
    event_repository.create(
        Event(
            id="event-battle-yavin",
            slug="battle-of-yavin",
            title="Battle of Yavin",
            description=None,
            start_year=0,
            end_year=0,
            era=None,
            canon_status=None,
        )
    )
    event_repository.create(
        Event(
            id="event-battle-crait",
            slug="battle-of-crait",
            title="Battle of Crait",
            description=None,
            start_year=34,
            end_year=34,
            era=None,
            canon_status=None,
        )
    )
    event_repository.create(
        Event(
            id="event-battle-exegol",
            slug="battle-of-exegol",
            title="Battle of Exegol",
            description=None,
            start_year=35,
            end_year=35,
            era=None,
            canon_status=None,
        )
    )

    character_repository = FakeCharacterRepository()
    for character in (
        Character("char-luke", "luke-skywalker", "Luke Skywalker", None, None, None),
        Character("char-leia", "leia-organa", "Leia Organa", None, None, None),
        Character("char-tarkin", "grand-moff-tarkin", "Grand Moff Tarkin", None, None, None),
        Character("char-palpatine", "sheev-palpatine", "Sheev Palpatine", None, None, None),
    ):
        character_repository.create(character)

    planet_repository = FakePlanetRepository()
    for planet in (
        Planet("planet-alderaan", "alderaan", "Alderaan", None, None),
        Planet("planet-coruscant", "coruscant", "Coruscant", None, None),
        Planet("planet-geonosis", "geonosis", "Geonosis", None, None),
        Planet("planet-naboo", "naboo", "Naboo", None, None),
    ):
        planet_repository.create(planet)

    faction_repository = FakeFactionRepository()
    for faction in (
        Faction("faction-republic", "galactic-republic", "Galactic Republic", None),
        Faction("faction-empire", "galactic-empire", "Galactic Empire", None),
        Faction("faction-cis", "cis", "Confederacy of Independent Systems", None),
    ):
        faction_repository.create(faction)

    graph_repository = FakeGraphRepository(
        nodes=[
            make_node("event-rise-empire", NodeType.EVENT),
            make_node("event-battle-yavin", NodeType.EVENT),
            make_node("event-battle-crait", NodeType.EVENT),
            make_node("event-battle-exegol", NodeType.EVENT),
            make_node("char-luke", NodeType.CHARACTER),
            make_node("char-leia", NodeType.CHARACTER),
            make_node("char-tarkin", NodeType.CHARACTER),
            make_node("char-palpatine", NodeType.CHARACTER),
            make_node("planet-alderaan", NodeType.PLANET),
            make_node("planet-coruscant", NodeType.PLANET),
            make_node("planet-geonosis", NodeType.PLANET),
            make_node("planet-naboo", NodeType.PLANET),
            make_node("faction-republic", NodeType.FACTION),
            make_node("faction-empire", NodeType.FACTION),
            make_node("faction-cis", NodeType.FACTION),
        ]
    )
    graph_repository.event_chronology_by_id = {
        "event-rise-empire": (-19, -19),
        "event-battle-yavin": (0, 0),
        "event-battle-crait": (34, 34),
        "event-battle-exegol": (35, 35),
    }
    relationship_service = RelationshipService(graph_repository)
    relationship_service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.SETS_PLANET_CONTROL,
            from_node_id="event-rise-empire",
            to_node_id="faction-empire",
            subject_node_id="planet-coruscant",
            note="Imperial takeover",
        )
    )
    relationship_service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.SETS_PLANET_CONTROL,
            from_node_id="event-rise-empire",
            to_node_id="faction-empire",
            subject_node_id="planet-alderaan",
            note="Imperial takeover",
        )
    )
    relationship_service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.SETS_PLANET_CONTROL,
            from_node_id="event-rise-empire",
            to_node_id="faction-empire",
            subject_node_id="planet-naboo",
            note="Imperial takeover",
        )
    )
    relationship_service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.SETS_ALIVE_STATE,
            from_node_id="event-battle-crait",
            to_node_id="char-luke",
            value_bool=False,
            note="Luke dies here",
        )
    )

    return UniverseStateService(
        event_repository=event_repository,
        character_repository=character_repository,
        planet_repository=planet_repository,
        faction_repository=faction_repository,
        graph_repository=graph_repository,
    )


def test_state_before_battle_of_yavin_uses_prior_mutations_only() -> None:
    UniverseStateService.invalidate_projection_cache()
    service = make_service()

    snapshot = service.get_state_before_event("event-battle-yavin")

    controls = {item.planet_slug: item.faction_slug for item in snapshot.faction_control}
    characters = {item.slug: item for item in snapshot.characters}

    assert snapshot.event_slug == "battle-of-yavin"
    assert controls["coruscant"] == "galactic-empire"
    assert characters["grand-moff-tarkin"].is_alive is True


def test_state_before_battle_of_exegol_includes_earlier_character_deaths() -> None:
    UniverseStateService.invalidate_projection_cache()
    service = make_service()

    snapshot = service.get_state_before_event("event-battle-exegol")

    characters = {item.slug: item for item in snapshot.characters}

    assert characters["luke-skywalker"].is_alive is False
    assert characters["sheev-palpatine"].is_alive is True


def test_state_projection_prefers_graph_mutation_edges_when_present() -> None:
    UniverseStateService.invalidate_projection_cache()
    event_repository = FakeEventRepository()
    event_repository.create(Event("event-rise-empire", "rise-of-the-empire", "Rise of the Empire", None, -19, -19, None, None))
    event_repository.create(Event("event-battle-yavin", "battle-of-yavin", "Battle of Yavin", None, 0, 0, None, None))

    character_repository = FakeCharacterRepository()
    character_repository.create(Character("char-tarkin", "grand-moff-tarkin", "Grand Moff Tarkin", None, None, None))
    character_repository.create(Character("char-palpatine", "sheev-palpatine", "Sheev Palpatine", None, None, None))

    planet_repository = FakePlanetRepository()
    planet_repository.create(Planet("planet-coruscant", "coruscant", "Coruscant", None, None))
    planet_repository.create(Planet("planet-naboo", "naboo", "Naboo", None, None))

    faction_repository = FakeFactionRepository()
    faction_repository.create(Faction("faction-republic", "galactic-republic", "Galactic Republic", None))
    faction_repository.create(Faction("faction-empire", "galactic-empire", "Galactic Empire", None))

    graph_repository = FakeGraphRepository(
        nodes=[
            make_node("event-rise-empire", NodeType.EVENT),
            make_node("event-battle-yavin", NodeType.EVENT),
            make_node("char-tarkin", NodeType.CHARACTER),
            make_node("char-palpatine", NodeType.CHARACTER),
            make_node("planet-coruscant", NodeType.PLANET),
            make_node("planet-naboo", NodeType.PLANET),
            make_node("faction-empire", NodeType.FACTION),
        ]
    )
    graph_repository.event_chronology_by_id = {
        "event-rise-empire": (-19, -19),
        "event-battle-yavin": (0, 0),
    }
    relationship_service = RelationshipService(graph_repository)
    relationship_service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.SETS_PLANET_CONTROL,
            from_node_id="event-rise-empire",
            to_node_id="faction-empire",
            subject_node_id="planet-coruscant",
            note="Imperial takeover",
        )
    )
    relationship_service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.SETS_ALIVE_STATE,
            from_node_id="event-rise-empire",
            to_node_id="char-palpatine",
            value_bool=True,
            note="Still alive",
        )
    )

    service = UniverseStateService(
        event_repository=event_repository,
        character_repository=character_repository,
        planet_repository=planet_repository,
        faction_repository=faction_repository,
        graph_repository=graph_repository,
    )

    snapshot = service.get_state_before_event("event-battle-yavin")

    controls = {item.planet_slug: item.faction_slug for item in snapshot.faction_control}
    assert snapshot.projection_mode == "graph-event-projection"
    assert controls["coruscant"] == "galactic-empire"


def test_state_without_graph_mutations_keeps_baseline_state() -> None:
    UniverseStateService.invalidate_projection_cache()
    event_repository = FakeEventRepository()
    event_repository.create(Event("event-battle-yavin", "battle-of-yavin", "Battle of Yavin", None, 0, 0, None, None))

    character_repository = FakeCharacterRepository()
    character_repository.create(Character("char-tarkin", "grand-moff-tarkin", "Grand Moff Tarkin", None, None, None))
    character_repository.create(Character("char-palpatine", "sheev-palpatine", "Sheev Palpatine", None, None, None))

    planet_repository = FakePlanetRepository()
    planet_repository.create(Planet("planet-coruscant", "coruscant", "Coruscant", None, None))
    planet_repository.create(Planet("planet-naboo", "naboo", "Naboo", None, None))
    planet_repository.create(Planet("planet-alderaan", "alderaan", "Alderaan", None, None))
    planet_repository.create(Planet("planet-geonosis", "geonosis", "Geonosis", None, None))

    faction_repository = FakeFactionRepository()
    faction_repository.create(Faction("faction-republic", "galactic-republic", "Galactic Republic", None))
    faction_repository.create(Faction("faction-empire", "galactic-empire", "Galactic Empire", None))
    faction_repository.create(Faction("faction-cis", "cis", "Confederacy of Independent Systems", None))

    graph_repository = FakeGraphRepository(nodes=[make_node("event-battle-yavin", NodeType.EVENT)])
    graph_repository.event_chronology_by_id = {"event-battle-yavin": (0, 0)}

    service = UniverseStateService(
        event_repository=event_repository,
        character_repository=character_repository,
        planet_repository=planet_repository,
        faction_repository=faction_repository,
        graph_repository=graph_repository,
    )

    snapshot = service.get_state_before_event("event-battle-yavin")

    controls = {item.planet_slug: item.faction_slug for item in snapshot.faction_control}
    characters = {item.slug: item for item in snapshot.characters}

    assert snapshot.projection_mode == "graph-event-projection"
    assert controls["coruscant"] == "galactic-republic"
    assert characters["grand-moff-tarkin"].is_alive is True


def test_projection_cache_reuses_loaded_mutations_across_service_instances() -> None:
    UniverseStateService.invalidate_projection_cache()
    service = make_service()
    graph_repository = service._graph_repository

    first_snapshot = service.get_state_before_event("event-battle-exegol")
    second_service = UniverseStateService(
        event_repository=service._event_repository,
        character_repository=service._character_repository,
        planet_repository=service._planet_repository,
        faction_repository=service._faction_repository,
        graph_repository=graph_repository,
    )
    second_snapshot = second_service.get_state_before_event("event-battle-yavin")

    assert first_snapshot.event_slug == "battle-of-exegol"
    assert second_snapshot.event_slug == "battle-of-yavin"
    assert graph_repository.list_state_mutations_before_event_calls == ["event-battle-exegol"]


def test_projection_cache_is_invalidated_after_new_relationship_write() -> None:
    UniverseStateService.invalidate_projection_cache()
    service = make_service()
    graph_repository = service._graph_repository

    initial_snapshot = service.get_state_before_event("event-battle-exegol")
    characters_before = {item.slug: item for item in initial_snapshot.characters}
    assert characters_before["sheev-palpatine"].is_alive is True
    assert graph_repository.list_state_mutations_before_event_calls == ["event-battle-exegol"]

    relationship_service = RelationshipService(graph_repository)
    relationship_service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.SETS_ALIVE_STATE,
            from_node_id="event-battle-crait",
            to_node_id="char-palpatine",
            value_bool=False,
            note="Checkpoint invalidation test",
        )
    )

    refreshed_snapshot = service.get_state_before_event("event-battle-exegol")
    characters_after = {item.slug: item for item in refreshed_snapshot.characters}

    assert characters_after["sheev-palpatine"].is_alive is False
    assert graph_repository.list_state_mutations_before_event_calls == [
        "event-battle-exegol",
        "event-battle-exegol",
    ]
