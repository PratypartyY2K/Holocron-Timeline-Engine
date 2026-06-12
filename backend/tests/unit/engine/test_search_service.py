import pytest

from app.domain.entities.search_result import SearchResult
from app.domain.errors import ValidationError
from app.engine.services.search_service import SearchService
from tests.unit.engine.fakes import FakeGraphRepository


def test_search_returns_matching_entities() -> None:
    repository = FakeGraphRepository()
    repository.search_results = [
        SearchResult(
            entity_type="character",
            id="char-1",
            slug="anakin-skywalker",
            label="Anakin Skywalker",
            description="Jedi Knight",
        ),
        SearchResult(
            entity_type="event",
            id="event-1",
            slug="order-66",
            label="Order 66",
            description="Clone protocol",
        ),
    ]
    service = SearchService(repository)

    results = service.search(query="anakin", limit=10)

    assert [item.slug for item in results] == ["anakin-skywalker"]


def test_search_rejects_blank_query() -> None:
    service = SearchService(FakeGraphRepository())

    with pytest.raises(ValidationError):
        service.search(query="   ", limit=10)


def test_search_rejects_non_positive_limit() -> None:
    service = SearchService(FakeGraphRepository())

    with pytest.raises(ValidationError):
        service.search(query="anakin", limit=0)
