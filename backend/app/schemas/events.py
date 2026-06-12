from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.domain.enums import RelationshipType


class CreateEventRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    start_year: int
    end_year: int | None = None
    era: str | None = Field(default=None, max_length=120)
    canon_status: str | None = Field(default=None, max_length=50)
    source_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_chronology(self) -> "CreateEventRequest":
        if self.end_year is not None and self.end_year < self.start_year:
            raise ValueError("end_year must be greater than or equal to start_year")
        return self


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    title: str
    description: str | None
    start_year: int
    end_year: int | None
    era: str | None
    canon_status: str | None
    source_refs: list[str]
    created_at: datetime
    updated_at: datetime


class EventListResponse(BaseModel):
    items: list[EventResponse]
    total: int
    limit: int
    offset: int


class CausalGraphEdgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    target_id: str
    type: RelationshipType
    note: str | None


class CausalGraphResponse(BaseModel):
    focus_event_id: str
    depth: int
    nodes: list[EventResponse]
    edges: list[CausalGraphEdgeResponse]


class EventImpactResponse(BaseModel):
    event_id: str
    impacted_events: list[EventResponse]
    broken_edges: list[CausalGraphEdgeResponse]
