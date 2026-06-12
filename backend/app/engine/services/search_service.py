from app.domain.entities.search_result import SearchResult
from app.domain.errors import ValidationError
from app.repositories.interfaces.graph_repository import GraphRepository


class SearchService:
    def __init__(self, graph_repository: GraphRepository) -> None:
        self._graph_repository = graph_repository

    def search(self, *, query: str, limit: int = 10) -> list[SearchResult]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValidationError("q must not be empty")
        if limit <= 0:
            raise ValidationError("limit must be greater than 0")
        return self._graph_repository.search_entities(query=normalized_query, limit=limit)
