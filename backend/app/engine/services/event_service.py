from uuid import uuid4

from app.domain.entities.causal_graph import CausalGraph
from app.domain.entities.event import Event
from app.domain.entities.event_impact import EventImpact
from app.domain.errors import (
    ChronologyError,
    DuplicateEntityError,
    EntityNotFoundError,
    ValidationError,
)
from app.engine.dto import CreateEventCommand, ListEventsQuery
from app.engine.services.universe_state_service import UniverseStateService
from app.repositories.interfaces.event_repository import EventRepository


class EventService:
    def __init__(self, event_repository: EventRepository) -> None:
        self._event_repository = event_repository

    def create_event(self, command: CreateEventCommand) -> Event:
        self._validate_create_command(command)

        if self._event_repository.get_by_slug(command.slug) is not None:
            raise DuplicateEntityError(f"Event slug already exists: {command.slug}")

        event = Event(
            id=str(uuid4()),
            slug=command.slug,
            title=command.title,
            description=command.description,
            start_year=command.start_year,
            end_year=command.end_year,
            era=command.era,
            canon_status=command.canon_status,
            source_refs=list(command.source_refs),
        )
        created = self._event_repository.create(event)
        UniverseStateService.invalidate_projection_cache()
        return created

    def get_event(self, event_id: str) -> Event:
        event = self._event_repository.get_by_id(event_id)
        if event is None:
            raise EntityNotFoundError(f"Event not found: {event_id}")
        return event

    def get_event_by_slug(self, slug: str) -> Event:
        event = self._event_repository.get_by_slug(slug)
        if event is None:
            raise EntityNotFoundError(f"Event not found for slug: {slug}")
        return event

    def list_events(self, query: ListEventsQuery) -> tuple[list[Event], int]:
        if query.limit <= 0:
            raise ValidationError("limit must be greater than 0")
        if query.offset < 0:
            raise ValidationError("offset must be greater than or equal to 0")
        if query.order not in {"asc", "desc"}:
            raise ValidationError("order must be 'asc' or 'desc'")
        if (
            query.start_year is not None
            and query.end_year is not None
            and query.end_year < query.start_year
        ):
            raise ChronologyError("end_year must be greater than or equal to start_year")
        if query.causal_depth is not None and query.causal_depth <= 0:
            raise ValidationError("causal_depth must be greater than 0")

        return self._event_repository.list_events(
            start_year=query.start_year,
            end_year=query.end_year,
            era=query.era,
            character=query.character,
            location=query.location,
            causal_depth=query.causal_depth,
            limit=query.limit,
            offset=query.offset,
            order=query.order,
        )

    def list_dependencies(self, event_id: str, depth: int | None = None) -> list[Event]:
        self.get_event(event_id)
        self._validate_depth(depth)
        return self._event_repository.list_dependencies(event_id, depth=depth)

    def list_consequences(self, event_id: str, depth: int | None = None) -> list[Event]:
        self.get_event(event_id)
        self._validate_depth(depth)
        return self._event_repository.list_consequences(event_id, depth=depth)

    def get_causal_graph(self, event_id: str, depth: int = 2) -> CausalGraph:
        self.get_event(event_id)
        self._validate_depth(depth)
        return self._event_repository.get_causal_graph(event_id, depth=depth)

    def get_impact(self, event_id: str) -> EventImpact:
        self.get_event(event_id)
        return self._event_repository.get_impact(event_id)

    @staticmethod
    def _validate_create_command(command: CreateEventCommand) -> None:
        if not command.slug.strip():
            raise ValidationError("slug must not be empty")
        if not command.title.strip():
            raise ValidationError("title must not be empty")
        if command.end_year is not None and command.end_year < command.start_year:
            raise ChronologyError("end_year must be greater than or equal to start_year")

    @staticmethod
    def _validate_depth(depth: int | None) -> None:
        if depth is not None and depth <= 0:
            raise ValidationError("depth must be greater than 0")
        if depth is not None and depth > 8:
            raise ValidationError("depth must be less than or equal to 8")
