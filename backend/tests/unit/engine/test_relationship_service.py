import pytest

from app.domain.enums import NodeType, RelationshipType
from app.domain.errors import ChronologyError, DuplicateEntityError, EntityNotFoundError, UnsupportedRelationshipError, ValidationError
from app.engine.dto import CreateRelationshipCommand
from app.engine.services.relationship_service import RelationshipService
from tests.unit.engine.fakes import FakeGraphRepository, make_node


def seed_event(repository: FakeGraphRepository, event_id: str, start_year: int, end_year: int | None = None) -> None:
    repository.event_chronology_by_id[event_id] = (start_year, end_year)


def test_create_faction_relationship_canonicalizes_edge_order() -> None:
    repository = FakeGraphRepository(
        nodes=[
            make_node("zzz-faction", NodeType.FACTION),
            make_node("aaa-faction", NodeType.FACTION),
        ]
    )
    service = RelationshipService(repository)

    relationship = service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.ALLIED_WITH,
            from_node_id="zzz-faction",
            to_node_id="aaa-faction",
            note="Temporary alliance",
        )
    )

    assert relationship.from_node_id == "aaa-faction"
    assert relationship.to_node_id == "zzz-faction"


def test_create_relationship_rejects_unknown_node() -> None:
    repository = FakeGraphRepository(nodes=[make_node("event-1", NodeType.EVENT)])
    service = RelationshipService(repository)

    with pytest.raises(EntityNotFoundError):
        service.create_relationship(
            CreateRelationshipCommand(
                type=RelationshipType.CAUSES,
                from_node_id="event-1",
                to_node_id="missing",
                note=None,
            )
        )


def test_create_relationship_rejects_unsupported_pairing() -> None:
    repository = FakeGraphRepository(
        nodes=[
            make_node("event-1", NodeType.EVENT),
            make_node("planet-1", NodeType.PLANET),
        ]
    )
    service = RelationshipService(repository)

    with pytest.raises(UnsupportedRelationshipError):
        service.create_relationship(
            CreateRelationshipCommand(
                type=RelationshipType.CAUSES,
                from_node_id="event-1",
                to_node_id="planet-1",
                note=None,
            )
        )


def test_create_event_causal_relationship_keeps_direction() -> None:
    repository = FakeGraphRepository(
        nodes=[
            make_node("event-1", NodeType.EVENT),
            make_node("event-2", NodeType.EVENT),
        ]
    )
    seed_event(repository, "event-1", -1)
    seed_event(repository, "event-2", 0)
    service = RelationshipService(repository)

    relationship = service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.CAUSES,
            from_node_id="event-1",
            to_node_id="event-2",
            note="Direct cause",
        )
    )

    assert relationship.from_node_id == "event-1"
    assert relationship.to_node_id == "event-2"


def test_create_character_located_in_planet_relationship_is_allowed() -> None:
    repository = FakeGraphRepository(
        nodes=[
            make_node("char-1", NodeType.CHARACTER),
            make_node("planet-1", NodeType.PLANET),
        ]
    )
    service = RelationshipService(repository)

    relationship = service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.LOCATED_IN,
            from_node_id="char-1",
            to_node_id="planet-1",
            note="Homeworld",
        )
    )

    assert relationship.from_node_id == "char-1"
    assert relationship.to_node_id == "planet-1"


def test_create_relationship_rejects_self_cycles() -> None:
    repository = FakeGraphRepository(nodes=[make_node("event-1", NodeType.EVENT)])
    seed_event(repository, "event-1", -1)
    service = RelationshipService(repository)

    with pytest.raises(ValidationError):
        service.create_relationship(
            CreateRelationshipCommand(
                type=RelationshipType.CAUSES,
                from_node_id="event-1",
                to_node_id="event-1",
                note=None,
            )
        )


def test_create_relationship_rejects_duplicates() -> None:
    repository = FakeGraphRepository(
        nodes=[
            make_node("event-1", NodeType.EVENT),
            make_node("event-2", NodeType.EVENT),
        ]
    )
    seed_event(repository, "event-1", -1)
    seed_event(repository, "event-2", 0)
    service = RelationshipService(repository)

    service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.CAUSES,
            from_node_id="event-1",
            to_node_id="event-2",
            note="Direct cause",
        )
    )

    with pytest.raises(DuplicateEntityError):
        service.create_relationship(
            CreateRelationshipCommand(
                type=RelationshipType.CAUSES,
                from_node_id="event-1",
                to_node_id="event-2",
                note="Duplicate cause",
            )
        )


def test_create_symmetric_relationship_rejects_duplicates_after_canonicalization() -> None:
    repository = FakeGraphRepository(
        nodes=[
            make_node("zzz-faction", NodeType.FACTION),
            make_node("aaa-faction", NodeType.FACTION),
        ]
    )
    service = RelationshipService(repository)

    service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.ALLIED_WITH,
            from_node_id="zzz-faction",
            to_node_id="aaa-faction",
            note="Temporary alliance",
        )
    )

    with pytest.raises(DuplicateEntityError):
        service.create_relationship(
            CreateRelationshipCommand(
                type=RelationshipType.ALLIED_WITH,
                from_node_id="aaa-faction",
                to_node_id="zzz-faction",
                note="Same relationship reversed",
            )
        )


def test_create_causes_relationship_rejects_indirect_cycles() -> None:
    repository = FakeGraphRepository(
        nodes=[
            make_node("event-1", NodeType.EVENT),
            make_node("event-2", NodeType.EVENT),
            make_node("event-3", NodeType.EVENT),
        ]
    )
    seed_event(repository, "event-1", -5)
    seed_event(repository, "event-2", -4)
    seed_event(repository, "event-3", -3)
    service = RelationshipService(repository)

    service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.CAUSES,
            from_node_id="event-1",
            to_node_id="event-2",
            note=None,
        )
    )
    service.create_relationship(
        CreateRelationshipCommand(
            type=RelationshipType.CAUSES,
            from_node_id="event-2",
            to_node_id="event-3",
            note=None,
        )
    )

    with pytest.raises(ValidationError, match="introduce a cycle"):
        service.create_relationship(
            CreateRelationshipCommand(
                type=RelationshipType.CAUSES,
                from_node_id="event-3",
                to_node_id="event-1",
                note=None,
            )
        )


def test_create_causes_relationship_rejects_impossible_chronology() -> None:
    repository = FakeGraphRepository(
        nodes=[
            make_node("event-1", NodeType.EVENT),
            make_node("event-2", NodeType.EVENT),
        ]
    )
    seed_event(repository, "event-1", 5)
    seed_event(repository, "event-2", 1)
    service = RelationshipService(repository)

    with pytest.raises(ChronologyError, match="ordering is impossible"):
        service.create_relationship(
            CreateRelationshipCommand(
                type=RelationshipType.CAUSES,
                from_node_id="event-1",
                to_node_id="event-2",
                note=None,
            )
        )
