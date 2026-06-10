from abc import ABC, abstractmethod

from app.domain.entities.node_reference import NodeReference
from app.domain.entities.relationship import Relationship


class GraphRepository(ABC):
    @abstractmethod
    def get_node_reference(self, node_id: str) -> NodeReference | None:
        raise NotImplementedError

    @abstractmethod
    def get_relationship(
        self,
        *,
        relationship_type: str,
        from_node_id: str,
        to_node_id: str,
    ) -> Relationship | None:
        raise NotImplementedError

    @abstractmethod
    def create_relationship(self, relationship: Relationship) -> Relationship:
        raise NotImplementedError
