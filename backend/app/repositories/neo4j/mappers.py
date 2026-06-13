from datetime import datetime
from typing import Any, cast

from app.domain.entities.character import Character
from app.domain.entities.event import Event
from app.domain.entities.faction import Faction
from app.domain.entities.node_reference import NodeReference
from app.domain.entities.planet import Planet
from app.domain.entities.relationship import Relationship
from app.domain.enums import NodeType, RelationshipType


def _datetime_value(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if hasattr(value, "to_native"):
        native_value = value.to_native()
        if isinstance(native_value, datetime):
            return native_value
    raise TypeError(f"Expected datetime value, got {type(value)!r}")


def map_event_record(properties: dict[str, Any]) -> Event:
    return Event(
        id=cast(str, properties["id"]),
        slug=cast(str, properties["slug"]),
        title=cast(str, properties["title"]),
        description=cast(str | None, properties.get("description")),
        start_year=cast(int, properties["start_year"]),
        end_year=cast(int | None, properties.get("end_year")),
        era=cast(str | None, properties.get("era")),
        canon_status=cast(str | None, properties.get("canon_status")),
        source_refs=list(cast(list[str] | None, properties.get("source_refs")) or []),
        created_at=_datetime_value(properties["created_at"]),
        updated_at=_datetime_value(properties["updated_at"]),
    )


def map_character_record(properties: dict[str, Any]) -> Character:
    return Character(
        id=cast(str, properties["id"]),
        slug=cast(str, properties["slug"]),
        name=cast(str, properties["name"]),
        description=cast(str | None, properties.get("description")),
        species=cast(str | None, properties.get("species")),
        homeworld_name=cast(str | None, properties.get("homeworld_name")),
        created_at=_datetime_value(properties["created_at"]),
        updated_at=_datetime_value(properties["updated_at"]),
    )


def map_planet_record(properties: dict[str, Any]) -> Planet:
    return Planet(
        id=cast(str, properties["id"]),
        slug=cast(str, properties["slug"]),
        name=cast(str, properties["name"]),
        description=cast(str | None, properties.get("description")),
        region=cast(str | None, properties.get("region")),
        created_at=_datetime_value(properties["created_at"]),
        updated_at=_datetime_value(properties["updated_at"]),
    )


def map_faction_record(properties: dict[str, Any]) -> Faction:
    return Faction(
        id=cast(str, properties["id"]),
        slug=cast(str, properties["slug"]),
        name=cast(str, properties["name"]),
        description=cast(str | None, properties.get("description")),
        created_at=_datetime_value(properties["created_at"]),
        updated_at=_datetime_value(properties["updated_at"]),
    )


def map_node_reference(record: dict[str, Any]) -> NodeReference:
    labels = cast(list[str], record["labels"])
    label = next(iter(labels), None)
    if label is None:
        raise ValueError("Node record had no labels")
    return NodeReference(
        id=cast(str, record["id"]),
        node_type=NodeType(label.lower()),
    )


def map_relationship_record(properties: dict[str, Any]) -> Relationship:
    return Relationship(
        id=cast(str, properties["id"]),
        type=RelationshipType(cast(str, properties["type"])),
        from_node_id=cast(str, properties["from_node_id"]),
        to_node_id=cast(str, properties["to_node_id"]),
        note=cast(str | None, properties.get("note")),
        subject_node_id=cast(str | None, properties.get("subject_node_id")),
        artifact_key=cast(str | None, properties.get("artifact_key")),
        value_bool=cast(bool | None, properties.get("value_bool")),
        value_text=cast(str | None, properties.get("value_text")),
        created_at=_datetime_value(properties["created_at"]),
        updated_at=_datetime_value(properties["updated_at"]),
    )
