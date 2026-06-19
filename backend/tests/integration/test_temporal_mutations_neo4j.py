import app.engine.services.universe_state_service as universe_state_module
from app.domain.entities.character import Character
from app.domain.entities.event import Event
from app.domain.entities.faction import Faction
from app.domain.entities.planet import Planet
from app.domain.enums import RelationshipType
from app.engine.dto import CreateRelationshipCommand
from app.engine.services.relationship_service import RelationshipService
from app.engine.services.universe_state_service import UniverseStateService
from app.repositories.neo4j.character_repository import Neo4jCharacterRepository
from app.repositories.neo4j.event_repository import Neo4jEventRepository
from app.repositories.neo4j.faction_repository import Neo4jFactionRepository
from app.repositories.neo4j.graph_repository import Neo4jGraphRepository
from app.repositories.neo4j.planet_repository import Neo4jPlanetRepository


def test_create_temporal_mutation_relationship_persists_payload_to_neo4j(
    neo4j_driver,
    integration_settings,
    integration_namespace: str,
) -> None:
    event_repository = Neo4jEventRepository(neo4j_driver, integration_settings)
    faction_repository = Neo4jFactionRepository(neo4j_driver, integration_settings)
    planet_repository = Neo4jPlanetRepository(neo4j_driver, integration_settings)
    graph_repository = Neo4jGraphRepository(neo4j_driver, integration_settings)
    relationship_service = RelationshipService(graph_repository)

    event = event_repository.create(
        Event(
            id=f"{integration_namespace}-event-rise-empire",
            slug=f"{integration_namespace}-rise-of-the-empire",
            title=f"{integration_namespace} Rise of the Empire",
            description=None,
            start_year=-19,
            end_year=-19,
            era=None,
            canon_status=None,
        )
    )
    faction = faction_repository.create(
        Faction(
            id=f"{integration_namespace}-faction-empire",
            slug=f"{integration_namespace}-galactic-empire",
            name=f"{integration_namespace} Galactic Empire",
            description=None,
        )
    )
    planet = planet_repository.create(
        Planet(
            id=f"{integration_namespace}-planet-coruscant",
            slug=f"{integration_namespace}-coruscant",
            name=f"{integration_namespace} Coruscant",
            description=None,
            region=None,
        )
    )

    created = relationship_service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.SETS_PLANET_CONTROL,
            from_node_id=event.id,
            to_node_id=faction.id,
            subject_node_id=planet.id,
            note="Integration test control flip",
        )
    )

    loaded = graph_repository.get_relationship(
        relationship_type=RelationshipType.SETS_PLANET_CONTROL.value,
        from_node_id=event.id,
        to_node_id=faction.id,
        subject_node_id=planet.id,
    )

    assert created.subject_node_id == planet.id
    assert loaded is not None
    assert loaded.subject_node_id == planet.id
    assert loaded.type is RelationshipType.SETS_PLANET_CONTROL


def test_universe_state_projection_reads_graph_mutations_from_neo4j(
    neo4j_driver,
    integration_settings,
    integration_namespace: str,
    monkeypatch,
) -> None:
    event_repository = Neo4jEventRepository(neo4j_driver, integration_settings)
    character_repository = Neo4jCharacterRepository(neo4j_driver, integration_settings)
    faction_repository = Neo4jFactionRepository(neo4j_driver, integration_settings)
    planet_repository = Neo4jPlanetRepository(neo4j_driver, integration_settings)
    graph_repository = Neo4jGraphRepository(neo4j_driver, integration_settings)
    relationship_service = RelationshipService(graph_repository)
    universe_state_service = UniverseStateService(
        event_repository=event_repository,
        character_repository=character_repository,
        planet_repository=planet_repository,
        faction_repository=faction_repository,
        graph_repository=graph_repository,
    )

    rise_empire = event_repository.create(
        Event(
            id=f"{integration_namespace}-event-rise-empire",
            slug=f"{integration_namespace}-rise-of-the-empire",
            title=f"{integration_namespace} Rise of the Empire",
            description=None,
            start_year=-19,
            end_year=-19,
            era=None,
            canon_status=None,
        )
    )
    battle_crait = event_repository.create(
        Event(
            id=f"{integration_namespace}-event-battle-crait",
            slug=f"{integration_namespace}-battle-of-crait",
            title=f"{integration_namespace} Battle of Crait",
            description=None,
            start_year=34,
            end_year=34,
            era=None,
            canon_status=None,
        )
    )
    battle_exegol = event_repository.create(
        Event(
            id=f"{integration_namespace}-event-battle-exegol",
            slug=f"{integration_namespace}-battle-of-exegol",
            title=f"{integration_namespace} Battle of Exegol",
            description=None,
            start_year=35,
            end_year=35,
            era=None,
            canon_status=None,
        )
    )

    luke = character_repository.create(
        Character(
            id=f"{integration_namespace}-char-luke",
            slug=f"{integration_namespace}-luke-skywalker",
            name=f"{integration_namespace} Luke Skywalker",
            description=None,
            species=None,
            homeworld_name=None,
        )
    )
    palpatine = character_repository.create(
        Character(
            id=f"{integration_namespace}-char-palpatine",
            slug=f"{integration_namespace}-sheev-palpatine",
            name=f"{integration_namespace} Sheev Palpatine",
            description=None,
            species=None,
            homeworld_name=None,
        )
    )

    empire = faction_repository.create(
        Faction(
            id=f"{integration_namespace}-faction-empire",
            slug=f"{integration_namespace}-galactic-empire",
            name=f"{integration_namespace} Galactic Empire",
            description=None,
        )
    )
    republic = faction_repository.create(
        Faction(
            id=f"{integration_namespace}-faction-republic",
            slug=f"{integration_namespace}-galactic-republic",
            name=f"{integration_namespace} Galactic Republic",
            description=None,
        )
    )
    cis = faction_repository.create(
        Faction(
            id=f"{integration_namespace}-faction-cis",
            slug=f"{integration_namespace}-cis",
            name=f"{integration_namespace} Confederacy of Independent Systems",
            description=None,
        )
    )
    _ = republic, cis

    alderaan = planet_repository.create(
        Planet(
            id=f"{integration_namespace}-planet-alderaan",
            slug=f"{integration_namespace}-alderaan",
            name=f"{integration_namespace} Alderaan",
            description=None,
            region=None,
        )
    )
    coruscant = planet_repository.create(
        Planet(
            id=f"{integration_namespace}-planet-coruscant",
            slug=f"{integration_namespace}-coruscant",
            name=f"{integration_namespace} Coruscant",
            description=None,
            region=None,
        )
    )
    naboo = planet_repository.create(
        Planet(
            id=f"{integration_namespace}-planet-naboo",
            slug=f"{integration_namespace}-naboo",
            name=f"{integration_namespace} Naboo",
            description=None,
            region=None,
        )
    )
    geonosis = planet_repository.create(
        Planet(
            id=f"{integration_namespace}-planet-geonosis",
            slug=f"{integration_namespace}-geonosis",
            name=f"{integration_namespace} Geonosis",
            description=None,
            region=None,
        )
    )
    _ = geonosis

    monkeypatch.setattr(
        universe_state_module,
        "TRACKED_CHARACTER_SLUGS",
        (luke.slug, palpatine.slug),
    )
    monkeypatch.setattr(
        universe_state_module,
        "BASELINE_CHARACTER_LOCATIONS",
        {palpatine.slug: coruscant.slug},
    )
    monkeypatch.setattr(
        universe_state_module,
        "BASELINE_PLANET_CONTROL",
        {
            alderaan.slug: republic.slug,
            coruscant.slug: republic.slug,
            geonosis.slug: cis.slug,
            naboo.slug: republic.slug,
        },
    )
    monkeypatch.setattr(universe_state_module, "BASELINE_ARTIFACTS", {})

    for planet in (alderaan, coruscant, naboo):
        relationship_service.create_relationship(
            CreateRelationshipCommand(
                type=RelationshipType.SETS_PLANET_CONTROL,
                from_node_id=rise_empire.id,
                to_node_id=empire.id,
                subject_node_id=planet.id,
                note="Integration test imperial control",
            )
        )

    relationship_service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.SETS_ALIVE_STATE,
            from_node_id=battle_crait.id,
            to_node_id=luke.id,
            value_bool=False,
            note="Luke dies at Crait",
        )
    )
    relationship_service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.SETS_ALIVE_STATE,
            from_node_id=battle_exegol.id,
            to_node_id=palpatine.id,
            value_bool=False,
            note="Palpatine dies at Exegol",
        )
    )

    snapshot = universe_state_service.get_state_before_event(battle_exegol.id)

    controls = {item.planet_slug: item.faction_slug for item in snapshot.faction_control}
    characters = {item.slug: item for item in snapshot.characters}

    assert snapshot.projection_mode == "graph-event-projection"
    assert controls[coruscant.slug] == empire.slug
    assert controls[alderaan.slug] == empire.slug
    assert controls[naboo.slug] == empire.slug
    assert characters[luke.slug].is_alive is False
    assert characters[palpatine.slug].is_alive is True
