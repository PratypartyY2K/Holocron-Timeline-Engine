from abc import ABC, abstractmethod

from app.domain.entities.planet import Planet


class PlanetRepository(ABC):
    @abstractmethod
    def create(self, planet: Planet) -> Planet:
        raise NotImplementedError

    @abstractmethod
    def get_by_slug(self, slug: str) -> Planet | None:
        raise NotImplementedError

    @abstractmethod
    def list_planets(self) -> list[Planet]:
        raise NotImplementedError
