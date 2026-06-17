from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.enums import NodeType, RelationshipType


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class NodeRefRecord(BaseModel):
    type: NodeType
    slug: str = Field(min_length=1, max_length=120)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return value.strip()


class EventRecord(BaseModel):
    slug: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    start_year: int
    end_year: int | None = None
    era: str | None = Field(default=None, max_length=120)
    canon_status: str | None = Field(default=None, max_length=50)
    source_refs: list[str] = Field(default_factory=list)

    @field_validator("slug", "title")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("description", "era", "canon_status")
    @classmethod
    def normalize_optional_text_fields(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("source_refs")
    @classmethod
    def normalize_source_refs(cls, values: list[str]) -> list[str]:
        normalized = [item.strip() for item in values if item.strip()]
        return list(dict.fromkeys(normalized))

    @model_validator(mode="after")
    def validate_chronology(self) -> "EventRecord":
        if self.end_year is not None and self.end_year < self.start_year:
            raise ValueError("end_year must be greater than or equal to start_year")
        return self


class CharacterRecord(BaseModel):
    slug: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    species: str | None = Field(default=None, max_length=120)
    homeworld_name: str | None = Field(default=None, max_length=120)

    @field_validator("slug", "name")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("description", "species", "homeworld_name")
    @classmethod
    def normalize_optional_text_fields(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)


class PlanetRecord(BaseModel):
    slug: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    region: str | None = Field(default=None, max_length=120)

    @field_validator("slug", "name")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("description", "region")
    @classmethod
    def normalize_optional_text_fields(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)


class FactionRecord(BaseModel):
    slug: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)

    @field_validator("slug", "name")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("description")
    @classmethod
    def normalize_optional_text_fields(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)


class RelationshipRecord(BaseModel):
    type: RelationshipType
    source: NodeRefRecord
    target: NodeRefRecord
    note: str | None = Field(default=None, max_length=1000)
    subject: NodeRefRecord | None = None
    artifact_key: str | None = Field(default=None, max_length=200)
    value_bool: bool | None = None
    value_text: str | None = Field(default=None, max_length=1000)

    @field_validator("note", "artifact_key", "value_text")
    @classmethod
    def normalize_optional_text_fields(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)


class PartialDataset(BaseModel):
    version: int = 1
    events: list[EventRecord] = Field(default_factory=list)
    characters: list[CharacterRecord] = Field(default_factory=list)
    planets: list[PlanetRecord] = Field(default_factory=list)
    factions: list[FactionRecord] = Field(default_factory=list)
    relationships: list[RelationshipRecord] = Field(default_factory=list)


class Dataset(PartialDataset):
    """Canonical processed dataset."""
