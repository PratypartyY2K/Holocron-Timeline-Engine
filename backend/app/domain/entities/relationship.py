from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.enums import RelationshipType


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Relationship:
    id: str
    type: RelationshipType
    from_node_id: str
    to_node_id: str
    note: str | None
    subject_node_id: str | None = None
    artifact_key: str | None = None
    value_bool: bool | None = None
    value_text: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
