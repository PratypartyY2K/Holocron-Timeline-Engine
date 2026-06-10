from abc import ABC, abstractmethod

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
