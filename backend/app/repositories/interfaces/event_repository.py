from abc import ABC, abstractmethod

from app.domain.entities.causal_graph import CausalGraph
from app.domain.entities.event import Event
from app.domain.entities.event_impact import EventImpact
from app.domain.entities.timeline_break_simulation import TimelineBreakSimulationGraph


class EventRepository(ABC):
    @abstractmethod
    def create(self, event: Event) -> Event:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, event_id: str) -> Event | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_slug(self, slug: str) -> Event | None:
        raise NotImplementedError

    @abstractmethod
    def list_events(
        self,
        *,
        start_year: int | None,
        end_year: int | None,
        era: str | None,
        character: str | None,
        location: str | None,
        causal_depth: int | None,
        limit: int,
        offset: int,
        order: str,
    ) -> tuple[list[Event], int]:
        raise NotImplementedError

    @abstractmethod
    def list_dependencies(self, event_id: str, depth: int | None = None) -> list[Event]:
        raise NotImplementedError

    @abstractmethod
    def list_consequences(self, event_id: str, depth: int | None = None) -> list[Event]:
        raise NotImplementedError

    @abstractmethod
    def get_causal_graph(self, event_id: str, depth: int) -> CausalGraph:
        raise NotImplementedError

    @abstractmethod
    def get_impact(self, event_id: str) -> EventImpact:
        raise NotImplementedError

    @abstractmethod
    def get_break_simulation_graph(self, event_id: str) -> TimelineBreakSimulationGraph:
        raise NotImplementedError
