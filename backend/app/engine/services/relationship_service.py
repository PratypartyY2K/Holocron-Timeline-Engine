from uuid import uuid4

from app.domain.entities.relationship import Relationship
from app.domain.enums import NodeType, RelationshipType
from app.domain.errors import DuplicateEntityError, EntityNotFoundError, UnsupportedRelationshipError, ValidationError
from app.engine.dto import CreateRelationshipCommand
from app.repositories.interfaces.graph_repository import GraphRepository


ALLOWED_RELATIONSHIP_NODE_TYPES: dict[RelationshipType, set[tuple[NodeType, NodeType]]] = {
    RelationshipType.CAUSES: {(NodeType.EVENT, NodeType.EVENT)},
    RelationshipType.INVOLVES: {
        (NodeType.EVENT, NodeType.CHARACTER),
        (NodeType.EVENT, NodeType.FACTION),
    },
    RelationshipType.LOCATED_IN: {
        (NodeType.EVENT, NodeType.PLANET),
        (NodeType.CHARACTER, NodeType.PLANET),
    },
    RelationshipType.MEMBER_OF: {(NodeType.CHARACTER, NodeType.FACTION)},
    RelationshipType.ALLIED_WITH: {(NodeType.FACTION, NodeType.FACTION)},
    RelationshipType.ENEMY_OF: {(NodeType.FACTION, NodeType.FACTION)},
}

CANONICAL_EDGE_TYPES: set[RelationshipType] = {
    RelationshipType.ALLIED_WITH,
    RelationshipType.ENEMY_OF,
}


class RelationshipService:
    def __init__(self, graph_repository: GraphRepository) -> None:
        self._graph_repository = graph_repository

    def create_relationship(self, command: CreateRelationshipCommand) -> Relationship:
        from_node = self._graph_repository.get_node_reference(command.from_node_id)
        if from_node is None:
            raise EntityNotFoundError(f"Node not found: {command.from_node_id}")

        to_node = self._graph_repository.get_node_reference(command.to_node_id)
        if to_node is None:
            raise EntityNotFoundError(f"Node not found: {command.to_node_id}")

        node_pair = (from_node.node_type, to_node.node_type)
        allowed_pairs = ALLOWED_RELATIONSHIP_NODE_TYPES[command.type]
        if node_pair not in allowed_pairs:
            raise UnsupportedRelationshipError(
                f"Relationship {command.type} is not valid for {from_node.node_type} -> {to_node.node_type}"
            )

        if command.from_node_id == command.to_node_id:
            raise ValidationError("self-referential relationships are not allowed")

        source_id = command.from_node_id
        target_id = command.to_node_id
        if command.type in CANONICAL_EDGE_TYPES and target_id < source_id:
            source_id, target_id = target_id, source_id

        existing_relationship = self._graph_repository.get_relationship(
            relationship_type=command.type.value,
            from_node_id=source_id,
            to_node_id=target_id,
        )
        if existing_relationship is not None:
            raise DuplicateEntityError(
                f"Relationship already exists: {command.type} {source_id} -> {target_id}"
            )

        relationship = Relationship(
            id=str(uuid4()),
            type=command.type,
            from_node_id=source_id,
            to_node_id=target_id,
            note=command.note,
        )
        return self._graph_repository.create_relationship(relationship)
