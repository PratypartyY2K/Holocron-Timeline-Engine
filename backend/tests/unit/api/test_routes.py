from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.domain.entities.relationship import Relationship
from app.domain.enums import RelationshipType
from app.domain.errors import UnsupportedRelationshipError
from app.engine.dto import CreateRelationshipCommand

from app.api.dependencies.services import get_event_service, get_relationship_service
from app.api.errors import register_exception_handlers
from app.api.router import api_router
from app.domain.entities.event import Event
from app.engine.services.event_service import EventService
from tests.unit.engine.fakes import FakeEventRepository


class RaisingRelationshipService:
    def create_relationship(self, command: CreateRelationshipCommand) -> Relationship:
        raise UnsupportedRelationshipError(
            f"Unsupported relationship type: {command.type.value}"
        )


def make_app(
    *,
    event_service: EventService | None = None,
    relationship_service: RaisingRelationshipService | None = None,
) -> FastAPI:
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")
    register_exception_handlers(app)

    if event_service is not None:
        app.dependency_overrides[get_event_service] = lambda: event_service
    if relationship_service is not None:
        app.dependency_overrides[get_relationship_service] = lambda: relationship_service

    return app


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


def to_api_datetime(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def test_get_event_returns_not_found_for_missing_event() -> None:
    app = make_app(event_service=EventService(FakeEventRepository()))
    client = TestClient(app)

    response = client.get("/api/v1/events/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Event not found: missing"}


def test_list_events_rejects_invalid_limit_at_http_boundary() -> None:
    app = make_app(event_service=EventService(FakeEventRepository()))
    client = TestClient(app)

    response = client.get("/api/v1/events", params={"limit": 0})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "limit"]


def test_create_event_rejects_invalid_chronology_payload() -> None:
    app = make_app(event_service=EventService(FakeEventRepository()))
    client = TestClient(app)

    response = client.post(
        "/api/v1/events",
        json={
            "slug": "bad-range",
            "title": "Bad Range",
            "description": None,
            "start_year": 5,
            "end_year": 4,
            "era": None,
            "canon_status": None,
            "source_refs": [],
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Value error, end_year must be greater than or equal to start_year"


def test_list_dependencies_returns_serialized_events() -> None:
    repository = FakeEventRepository()
    focus = make_event("event-1", "battle-of-yavin", 0)
    dependency = make_event("event-2", "steal-death-star-plans", -1)
    repository.create(focus)
    repository.create(dependency)
    repository.dependencies[focus.id] = [dependency]

    app = make_app(event_service=EventService(repository))
    client = TestClient(app)

    response = client.get(f"/api/v1/events/{focus.id}/dependencies", params={"depth": 2})

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": dependency.id,
            "slug": dependency.slug,
            "title": dependency.title,
            "description": None,
            "start_year": dependency.start_year,
            "end_year": dependency.end_year,
            "era": None,
            "canon_status": None,
            "dependency_count": 0,
            "centrality_score": 0.0,
            "source_refs": [],
            "faction_slugs": [],
            "faction_names": [],
            "created_at": to_api_datetime(dependency.created_at),
            "updated_at": to_api_datetime(dependency.updated_at),
        }
    ]


def test_create_relationship_maps_domain_errors_to_bad_request() -> None:
    app = make_app(relationship_service=RaisingRelationshipService())
    client = TestClient(app)

    response = client.post(
        "/api/v1/graph/relationships",
        json={
            "type": RelationshipType.CAUSES.value,
            "from_node_id": "event-1",
            "to_node_id": "planet-1",
            "note": None,
            "subject_node_id": None,
            "artifact_key": None,
            "value_bool": None,
            "value_text": None,
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Unsupported relationship type: CAUSES"}
