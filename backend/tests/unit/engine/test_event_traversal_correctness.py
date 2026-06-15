from app.domain.entities.causal_graph import CausalGraph, CausalGraphEdge
from app.domain.entities.event import Event
from app.domain.enums import RelationshipType
from app.engine.services.event_service import EventService
from tests.unit.engine.fakes import FakeEventRepository


def make_event(event_id: str, slug: str, start_year: int) -> Event:
    return Event(
        id=event_id,
        slug=slug,
        title=slug.replace("-", " ").title(),
        description=None,
        start_year=start_year,
        end_year=start_year,
        era=None,
        canon_status=None,
    )


def test_list_dependencies_returns_seeded_upstream_chain() -> None:
    repository = FakeEventRepository()
    origin = make_event("event-1", "steal-death-star-plans", -1)
    focus = make_event("event-2", "battle-of-yavin", 0)
    for event in (origin, focus):
        repository.create(event)
    repository.dependencies[focus.id] = [origin]

    dependencies = EventService(repository).list_dependencies(focus.id, depth=1)

    assert [event.id for event in dependencies] == [origin.id]
    assert [event.slug for event in dependencies] == [origin.slug]


def test_list_consequences_returns_seeded_downstream_chain() -> None:
    repository = FakeEventRepository()
    focus = make_event("event-1", "order-66", -19)
    consequence = make_event("event-2", "jedi-purge", -18)
    for event in (focus, consequence):
        repository.create(event)
    repository.consequences[focus.id] = [consequence]

    consequences = EventService(repository).list_consequences(focus.id, depth=2)

    assert [event.id for event in consequences] == [consequence.id]
    assert [event.slug for event in consequences] == [consequence.slug]


def test_get_causal_graph_returns_expected_nodes_and_edges() -> None:
    repository = FakeEventRepository()
    focus = make_event("event-1", "order-66", -19)
    upstream = make_event("event-2", "temple-bombing", -19)
    downstream = make_event("event-3", "jedi-purge", -18)
    for event in (focus, upstream, downstream):
        repository.create(event)
    repository.causal_graphs[(focus.id, 2)] = CausalGraph(
        focus_event_id=focus.id,
        depth=2,
        nodes=[upstream, focus, downstream],
        edges=[
            CausalGraphEdge(
                id="edge-1",
                source_id=upstream.id,
                target_id=focus.id,
                type=RelationshipType.CAUSES,
                note="Leads into Order 66",
            ),
            CausalGraphEdge(
                id="edge-2",
                source_id=focus.id,
                target_id=downstream.id,
                type=RelationshipType.CAUSES,
                note="Triggers purge",
            ),
        ],
    )

    graph = EventService(repository).get_causal_graph(focus.id, depth=2)

    assert graph.focus_event_id == focus.id
    assert [event.id for event in graph.nodes] == [upstream.id, focus.id, downstream.id]
    assert [(edge.source_id, edge.target_id) for edge in graph.edges] == [
        (upstream.id, focus.id),
        (focus.id, downstream.id),
    ]
