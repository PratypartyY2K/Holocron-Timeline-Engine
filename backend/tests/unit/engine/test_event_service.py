import pytest

from app.domain.entities.event import Event
from app.domain.errors import ChronologyError, DuplicateEntityError, EntityNotFoundError, ValidationError
from app.engine.dto import CreateEventCommand, ListEventsQuery
from app.engine.services.event_service import EventService
from tests.unit.engine.fakes import FakeEventRepository


def test_create_event_persists_to_repository() -> None:
    repository = FakeEventRepository()
    service = EventService(repository)

    event = service.create_event(
        CreateEventCommand(
            slug="battle-of-yavin",
            title="Battle of Yavin",
            description="The Rebel Alliance destroys the first Death Star.",
            start_year=0,
            end_year=0,
            era="Galactic Civil War",
            canon_status="canon",
            source_refs=["ANH"],
        )
    )

    assert repository.get_by_id(event.id) == event
    assert event.slug == "battle-of-yavin"


def test_create_event_rejects_duplicate_slug() -> None:
    repository = FakeEventRepository()
    service = EventService(repository)
    repository.create(
        Event(
            id="event-1",
            slug="order-66",
            title="Order 66",
            description=None,
            start_year=-19,
            end_year=None,
            era=None,
            canon_status=None,
        )
    )

    with pytest.raises(DuplicateEntityError):
        service.create_event(
            CreateEventCommand(
                slug="order-66",
                title="Order Sixty-Six",
                description=None,
                start_year=-19,
                end_year=None,
                era=None,
                canon_status=None,
            )
        )


def test_create_event_rejects_invalid_chronology() -> None:
    service = EventService(FakeEventRepository())

    with pytest.raises(ChronologyError):
        service.create_event(
            CreateEventCommand(
                slug="bad-range",
                title="Bad Range",
                description=None,
                start_year=5,
                end_year=4,
                era=None,
                canon_status=None,
            )
        )


def test_get_event_raises_when_missing() -> None:
    service = EventService(FakeEventRepository())

    with pytest.raises(EntityNotFoundError):
        service.get_event("missing")


def test_list_events_validates_query() -> None:
    service = EventService(FakeEventRepository())

    with pytest.raises(ValidationError):
        service.list_events(ListEventsQuery(limit=0))


def test_list_events_validates_causal_depth() -> None:
    service = EventService(FakeEventRepository())

    with pytest.raises(ValidationError):
        service.list_events(ListEventsQuery(causal_depth=0))


def test_list_events_supports_combined_filters() -> None:
    repository = FakeEventRepository()
    repository.create(
        Event(
            id="event-1",
            slug="battle-of-yavin",
            title="Battle of Yavin",
            description=None,
            start_year=0,
            end_year=0,
            era="Age of Rebellion",
            canon_status=None,
        )
    )
    repository.create(
        Event(
            id="event-2",
            slug="fall-of-the-empire",
            title="Fall of the Empire",
            description=None,
            start_year=4,
            end_year=4,
            era="New Republic",
            canon_status=None,
        )
    )
    service = EventService(repository)

    events, total = service.list_events(ListEventsQuery(era="Age of Rebellion"))

    assert total == 1
    assert [event.id for event in events] == ["event-1"]


def test_list_dependencies_requires_existing_event() -> None:
    service = EventService(FakeEventRepository())

    with pytest.raises(EntityNotFoundError):
        service.list_dependencies("missing")


def test_list_dependencies_passes_depth_to_repository() -> None:
    repository = FakeEventRepository()
    repository.create(
        Event(
            id="event-1",
            slug="battle-of-yavin",
            title="Battle of Yavin",
            description=None,
            start_year=0,
            end_year=0,
            era=None,
            canon_status=None,
        )
    )
    service = EventService(repository)

    service.list_dependencies("event-1", depth=2)

    assert repository.last_dependencies_depth == 2


def test_list_consequences_passes_depth_to_repository() -> None:
    repository = FakeEventRepository()
    repository.create(
        Event(
            id="event-1",
            slug="battle-of-yavin",
            title="Battle of Yavin",
            description=None,
            start_year=0,
            end_year=0,
            era=None,
            canon_status=None,
        )
    )
    service = EventService(repository)

    service.list_consequences("event-1", depth=3)

    assert repository.last_consequences_depth == 3


def test_dependency_depth_must_be_positive() -> None:
    repository = FakeEventRepository()
    repository.create(
        Event(
            id="event-1",
            slug="battle-of-yavin",
            title="Battle of Yavin",
            description=None,
            start_year=0,
            end_year=0,
            era=None,
            canon_status=None,
        )
    )
    service = EventService(repository)

    with pytest.raises(ValidationError):
        service.list_dependencies("event-1", depth=0)


def test_get_causal_graph_passes_depth_to_repository() -> None:
    repository = FakeEventRepository()
    repository.create(
        Event(
            id="event-1",
            slug="battle-of-yavin",
            title="Battle of Yavin",
            description=None,
            start_year=0,
            end_year=0,
            era=None,
            canon_status=None,
        )
    )
    service = EventService(repository)

    graph = service.get_causal_graph("event-1", depth=4)

    assert graph.focus_event_id == "event-1"
    assert graph.depth == 4
    assert repository.last_causal_graph_depth == 4
