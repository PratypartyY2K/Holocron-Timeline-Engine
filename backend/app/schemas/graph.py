from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import RelationshipType


class CreateRelationshipRequest(BaseModel):
    type: RelationshipType
    from_node_id: str = Field(min_length=1)
    to_node_id: str = Field(min_length=1)
    note: str | None = Field(default=None, max_length=1000)


class RelationshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: RelationshipType
    from_node_id: str
    to_node_id: str
    note: str | None
    created_at: datetime
    updated_at: datetime

