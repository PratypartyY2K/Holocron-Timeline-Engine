from dataclasses import dataclass

from app.domain.enums import NodeType


@dataclass(slots=True, frozen=True)
class NodeReference:
    id: str
    node_type: NodeType
