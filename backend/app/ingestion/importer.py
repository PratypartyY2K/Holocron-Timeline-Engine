from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.enums import NodeType
from app.domain.errors import DuplicateEntityError, EntityNotFoundError
from app.engine.dto import (
    CreateCharacterCommand,
    CreateEventCommand,
    CreateFactionCommand,
    CreatePlanetCommand,
    CreateRelationshipCommand,
)
from app.engine.services.character_service import CharacterService
from app.engine.services.event_service import EventService
from app.engine.services.faction_service import FactionService
from app.engine.services.planet_service import PlanetService
from app.engine.services.relationship_service import RelationshipService
from app.ingestion.models import (
    CharacterRecord,
    Dataset,
    EventRecord,
    FactionRecord,
    NodeRefRecord,
    PlanetRecord,
    RelationshipRecord,
)


@dataclass(slots=True)
class ImportCounter:
    created: int = 0
    skipped: int = 0


@dataclass(slots=True)
class DatasetImportResult:
    events: ImportCounter = field(default_factory=ImportCounter)
    characters: ImportCounter = field(default_factory=ImportCounter)
    planets: ImportCounter = field(default_factory=ImportCounter)
    factions: ImportCounter = field(default_factory=ImportCounter)
    relationships: ImportCounter = field(default_factory=ImportCounter)


class DatasetImporter:
    def __init__(
        self,
        *,
        event_service: EventService,
        character_service: CharacterService,
        planet_service: PlanetService,
        faction_service: FactionService,
        relationship_service: RelationshipService,
    ) -> None:
        self._event_service = event_service
        self._character_service = character_service
        self._planet_service = planet_service
        self._faction_service = faction_service
        self._relationship_service = relationship_service

    def import_dataset(self, dataset: Dataset) -> DatasetImportResult:
        result = DatasetImportResult()

        for event in dataset.events:
            self._ensure_event(event, result.events)
        for character in dataset.characters:
            self._ensure_character(character, result.characters)
        for planet in dataset.planets:
            self._ensure_planet(planet, result.planets)
        for faction in dataset.factions:
            self._ensure_faction(faction, result.factions)
        for relationship in dataset.relationships:
            self._ensure_relationship(relationship, result.relationships)

        return result

    def _ensure_event(self, record: EventRecord, counter: ImportCounter) -> str:
        try:
            existing = self._event_service.get_event_by_slug(record.slug)
        except EntityNotFoundError:
            created = self._event_service.create_event(
                CreateEventCommand(
                    slug=record.slug,
                    title=record.title,
                    description=record.description,
                    start_year=record.start_year,
                    end_year=record.end_year,
                    era=record.era,
                    canon_status=record.canon_status,
                    source_refs=record.source_refs,
                )
            )
            counter.created += 1
            return created.id
        counter.skipped += 1
        return existing.id

    def _ensure_character(self, record: CharacterRecord, counter: ImportCounter) -> str:
        try:
            existing = self._character_service.get_character_by_slug(record.slug)
        except EntityNotFoundError:
            created = self._character_service.create_character(
                CreateCharacterCommand(
                    slug=record.slug,
                    name=record.name,
                    description=record.description,
                    species=record.species,
                    homeworld_name=record.homeworld_name,
                )
            )
            counter.created += 1
            return created.id
        counter.skipped += 1
        return existing.id

    def _ensure_planet(self, record: PlanetRecord, counter: ImportCounter) -> str:
        try:
            existing = self._planet_service.get_planet_by_slug(record.slug)
        except EntityNotFoundError:
            created = self._planet_service.create_planet(
                CreatePlanetCommand(
                    slug=record.slug,
                    name=record.name,
                    description=record.description,
                    region=record.region,
                )
            )
            counter.created += 1
            return created.id
        counter.skipped += 1
        return existing.id

    def _ensure_faction(self, record: FactionRecord, counter: ImportCounter) -> str:
        try:
            existing = self._faction_service.get_faction_by_slug(record.slug)
        except EntityNotFoundError:
            created = self._faction_service.create_faction(
                CreateFactionCommand(
                    slug=record.slug,
                    name=record.name,
                    description=record.description,
                )
            )
            counter.created += 1
            return created.id
        counter.skipped += 1
        return existing.id

    def _ensure_relationship(self, record: RelationshipRecord, counter: ImportCounter) -> None:
        try:
            self._relationship_service.create_relationship(
                CreateRelationshipCommand(
                    type=record.type,
                    from_node_id=self._resolve_node_id(record.source),
                    to_node_id=self._resolve_node_id(record.target),
                    note=record.note,
                    subject_node_id=self._resolve_node_id(record.subject)
                    if record.subject is not None
                    else None,
                    artifact_key=record.artifact_key,
                    value_bool=record.value_bool,
                    value_text=record.value_text,
                )
            )
        except DuplicateEntityError:
            counter.skipped += 1
        else:
            counter.created += 1

    def _resolve_node_id(self, ref: NodeRefRecord) -> str:
        if ref.type is NodeType.EVENT:
            return self._event_service.get_event_by_slug(ref.slug).id
        if ref.type is NodeType.CHARACTER:
            return self._character_service.get_character_by_slug(ref.slug).id
        if ref.type is NodeType.PLANET:
            return self._planet_service.get_planet_by_slug(ref.slug).id
        if ref.type is NodeType.FACTION:
            return self._faction_service.get_faction_by_slug(ref.slug).id
        raise ValueError(f"Unsupported node type: {ref.type}")
