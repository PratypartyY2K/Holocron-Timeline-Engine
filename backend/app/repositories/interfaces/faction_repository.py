from abc import ABC, abstractmethod

from app.domain.entities.character import Character
from app.domain.entities.event import Event
from app.domain.entities.faction import Faction


class FactionRepository(ABC):
    @abstractmethod
    def create(self, faction: Faction) -> Faction:
        raise NotImplementedError

    @abstractmethod
    def get_by_slug(self, slug: str) -> Faction | None:
        raise NotImplementedError

    @abstractmethod
    def list_factions(self) -> list[Faction]:
        raise NotImplementedError

    @abstractmethod
    def list_related_characters(self, slug: str) -> list[Character]:
        raise NotImplementedError

    @abstractmethod
    def list_enemy_factions(self, slug: str) -> list[Faction]:
        raise NotImplementedError

    @abstractmethod
    def list_involved_events(self, slug: str) -> list[Event]:
        raise NotImplementedError
