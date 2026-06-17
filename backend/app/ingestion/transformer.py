from __future__ import annotations

import json
from pathlib import Path

from app.ingestion.models import (
    CharacterRecord,
    Dataset,
    EventRecord,
    FactionRecord,
    PartialDataset,
    PlanetRecord,
    RelationshipRecord,
)


def load_partial_dataset(path: Path) -> PartialDataset:
    return PartialDataset.model_validate_json(path.read_text())


def load_processed_dataset(path: Path) -> Dataset:
    return Dataset.model_validate_json(path.read_text())


def transform_raw_directory(raw_dir: Path) -> Dataset:
    partials = [load_partial_dataset(path) for path in sorted(raw_dir.rglob("*.json"))]
    return merge_partials(partials)


def write_processed_dataset(dataset: Dataset, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(dataset.model_dump_json(indent=2) + "\n")


def merge_partials(partials: list[PartialDataset]) -> Dataset:
    events: dict[str, EventRecord] = {}
    characters: dict[str, CharacterRecord] = {}
    planets: dict[str, PlanetRecord] = {}
    factions: dict[str, FactionRecord] = {}
    relationships: dict[tuple[object, ...], RelationshipRecord] = {}

    for partial in partials:
        for event in partial.events:
            _merge_unique(events, event.slug, event, "event")
        for character in partial.characters:
            _merge_unique(characters, character.slug, character, "character")
        for planet in partial.planets:
            _merge_unique(planets, planet.slug, planet, "planet")
        for faction in partial.factions:
            _merge_unique(factions, faction.slug, faction, "faction")
        for relationship in partial.relationships:
            key = relationship_key(relationship)
            _merge_unique(relationships, key, relationship, "relationship")

    return Dataset(
        version=1,
        events=sorted(events.values(), key=lambda item: (item.start_year, item.slug)),
        characters=sorted(characters.values(), key=lambda item: item.slug),
        planets=sorted(planets.values(), key=lambda item: item.slug),
        factions=sorted(factions.values(), key=lambda item: item.slug),
        relationships=sorted(relationships.values(), key=sort_relationship_key),
    )


def relationship_key(relationship: RelationshipRecord) -> tuple[object, ...]:
    return (
        relationship.type,
        relationship.source.type,
        relationship.source.slug,
        relationship.target.type,
        relationship.target.slug,
        relationship.subject.type if relationship.subject is not None else None,
        relationship.subject.slug if relationship.subject is not None else None,
        relationship.artifact_key,
        relationship.value_bool,
        relationship.value_text,
        relationship.note,
    )


def sort_relationship_key(relationship: RelationshipRecord) -> tuple[object, ...]:
    return (
        relationship.type.value,
        relationship.source.type.value,
        relationship.source.slug,
        relationship.target.type.value,
        relationship.target.slug,
        relationship.subject.type.value if relationship.subject is not None else "",
        relationship.subject.slug if relationship.subject is not None else "",
        relationship.artifact_key or "",
    )


def _merge_unique(store: dict[object, object], key: object, value: object, label: str) -> None:
    existing = store.get(key)
    if existing is not None and existing != value:
        raise ValueError(f"Conflicting duplicate {label}: {key}")
    store[key] = value

