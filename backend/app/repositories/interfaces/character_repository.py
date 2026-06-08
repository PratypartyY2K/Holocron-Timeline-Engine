from abc import ABC, abstractmethod

from app.domain.entities.character import Character


class CharacterRepository(ABC):
    @abstractmethod
    def create(self, character: Character) -> Character:
        raise NotImplementedError

    @abstractmethod
    def get_by_slug(self, slug: str) -> Character | None:
        raise NotImplementedError
