from uuid import uuid4

from app.domain.entities.relationship import Relationship
from app.domain.enums import NodeType, RelationshipType
from app.domain.errors import (
    ChronologyError,
    DuplicateEntityError,
    EntityNotFoundError,
    UnsupportedRelationshipError,
    ValidationError,
)
from app.engine.dto import CreateRelationshipCommand
from app.engine.services.universe_state_service import UniverseStateService
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
    RelationshipType.SETS_ALIVE_STATE: {(NodeType.EVENT, NodeType.CHARACTER)},
    RelationshipType.SETS_CHARACTER_LOCATION: {(NodeType.EVENT, NodeType.PLANET)},
    RelationshipType.SETS_PLANET_CONTROL: {(NodeType.EVENT, NodeType.FACTION)},
    RelationshipType.SETS_ARTIFACT_LOCATION: {
        (NodeType.EVENT, NodeType.CHARACTER),
        (NodeType.EVENT, NodeType.PLANET),
    },
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
        if command.type is RelationshipType.CAUSES:
            self._validate_causes_relationship(source_id=source_id, target_id=target_id)
        else:
            self._validate_temporal_mutation(command=command)

        if command.type in CANONICAL_EDGE_TYPES and target_id < source_id:
            # These relationships are logically undirected, so we normalize storage to keep
            # duplicate detection predictable.
            source_id, target_id = target_id, source_id

        existing_relationship = self._graph_repository.get_relationship(
            relationship_type=command.type.value,
            from_node_id=source_id,
            to_node_id=target_id,
            subject_node_id=command.subject_node_id,
            artifact_key=command.artifact_key,
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
            subject_node_id=command.subject_node_id,
            artifact_key=command.artifact_key,
            value_bool=command.value_bool,
            value_text=command.value_text,
        )
        created = self._graph_repository.create_relationship(relationship)
        UniverseStateService.invalidate_projection_cache()
        return created

    def _validate_causes_relationship(self, *, source_id: str, target_id: str) -> None:
        if self._graph_repository.causes_path_exists(from_node_id=target_id, to_node_id=source_id):
            raise ValidationError(
                f"CAUSES relationship would introduce a cycle: {source_id} -> {target_id}"
            )

        source_chronology = self._graph_repository.get_event_chronology(source_id)
        if source_chronology is None:
            raise EntityNotFoundError(f"Event not found: {source_id}")

        target_chronology = self._graph_repository.get_event_chronology(target_id)
        if target_chronology is None:
            raise EntityNotFoundError(f"Event not found: {target_id}")

        source_start_year, _ = source_chronology
        target_start_year, _ = target_chronology
        if source_start_year > target_start_year:
            raise ChronologyError(
                "CAUSES relationship ordering is impossible: "
                f"source event starts after target event ({source_start_year} > {target_start_year})"
            )

    def _validate_temporal_mutation(self, command: CreateRelationshipCommand) -> None:
        if command.type is RelationshipType.SETS_ALIVE_STATE and command.value_bool is None:
            raise ValidationError("SETS_ALIVE_STATE requires value_bool")

        if command.type is RelationshipType.SETS_CHARACTER_LOCATION:
            self._require_subject_node(
                command.subject_node_id,
                "SETS_CHARACTER_LOCATION requires subject_node_id",
            )
            self._validate_subject_type(command.subject_node_id, NodeType.CHARACTER)

        if command.type is RelationshipType.SETS_PLANET_CONTROL:
            self._require_subject_node(
                command.subject_node_id,
                "SETS_PLANET_CONTROL requires subject_node_id",
            )
            self._validate_subject_type(command.subject_node_id, NodeType.PLANET)

        if command.type is RelationshipType.SETS_ARTIFACT_LOCATION:
            if command.artifact_key is None or not command.artifact_key.strip():
                raise ValidationError("SETS_ARTIFACT_LOCATION requires artifact_key")

    def _require_subject_node(self, subject_node_id: str | None, message: str) -> None:
        if subject_node_id is None or not subject_node_id.strip():
            raise ValidationError(message)

    def _validate_subject_type(self, subject_node_id: str | None, expected_type: NodeType) -> None:
        if subject_node_id is None:
            raise ValidationError("subject_node_id is required")
        node = self._graph_repository.get_node_reference(subject_node_id)
        if node is None:
            raise EntityNotFoundError(f"Node not found: {subject_node_id}")
        if node.node_type is not expected_type:
            raise UnsupportedRelationshipError(
                f"Temporal mutation subject must be {expected_type}, got {node.node_type}"
            )
