from collections.abc import Mapping
from dataclasses import dataclass

from app.domain.entities.character import Character
from app.domain.entities.event import Event
from app.domain.entities.faction import Faction
from app.domain.entities.planet import Planet
from app.domain.enums import RelationshipType
from app.domain.errors import DuplicateEntityError
from app.engine.dto import CreateRelationshipCommand
from app.engine.services.relationship_service import RelationshipService
from app.engine.universe_state_catalog import (
    CHARACTER_SLUG_ALIASES,
    MUTATION_ALIASES,
    ArtifactMutation,
    EventStateMutation,
)
from app.repositories.interfaces.character_repository import CharacterRepository
from app.repositories.interfaces.event_repository import EventRepository
from app.repositories.interfaces.faction_repository import FactionRepository
from app.repositories.interfaces.planet_repository import PlanetRepository


@dataclass(frozen=True, slots=True)
class PlannedTemporalMutation:
    event_slug: str
    relationship_type: RelationshipType
    to_node_id: str
    subject_node_id: str | None = None
    artifact_key: str | None = None
    value_bool: bool | None = None
    note: str | None = None


@dataclass(frozen=True, slots=True)
class TemporalMutationBackfillResult:
    applied: int
    skipped_duplicates: int
    planned: int
    missing_events: tuple[str, ...] = ()
    skipped_missing_entities: tuple[str, ...] = ()
    details: tuple[str, ...] = ()


class TemporalMutationBackfillService:
    def __init__(
        self,
        *,
        event_repository: EventRepository,
        character_repository: CharacterRepository,
        planet_repository: PlanetRepository,
        faction_repository: FactionRepository,
        relationship_service: RelationshipService,
    ) -> None:
        self._event_repository = event_repository
        self._character_repository = character_repository
        self._planet_repository = planet_repository
        self._faction_repository = faction_repository
        self._relationship_service = relationship_service

    def backfill(self, *, dry_run: bool = False) -> TemporalMutationBackfillResult:
        plans, missing_events, skipped_missing_entities = self._build_plan()
        applied = 0
        skipped_duplicates = 0
        details: list[str] = []

        for event, plan in plans:
            description = self._describe(event.slug, plan)
            details.append(description)
            if dry_run:
                continue

            try:
                self._relationship_service.create_relationship(
                    CreateRelationshipCommand(
                        type=plan.relationship_type,
                        from_node_id=event.id,
                        to_node_id=plan.to_node_id,
                        subject_node_id=plan.subject_node_id,
                        artifact_key=plan.artifact_key,
                        value_bool=plan.value_bool,
                        note=plan.note,
                    )
                )
                applied += 1
            except DuplicateEntityError:
                skipped_duplicates += 1

        return TemporalMutationBackfillResult(
            applied=applied,
            skipped_duplicates=skipped_duplicates,
            planned=len(plans),
            missing_events=tuple(missing_events),
            skipped_missing_entities=tuple(skipped_missing_entities),
            details=tuple(details),
        )

    def _build_plan(
        self,
    ) -> tuple[list[tuple[Event, PlannedTemporalMutation]], list[str], list[str]]:
        characters_by_slug = {
            item.slug: item for item in self._character_repository.list_characters()
        }
        planets_by_slug = {item.slug: item for item in self._planet_repository.list_planets()}
        factions_by_slug = {item.slug: item for item in self._faction_repository.list_factions()}

        plans: list[tuple[Event, PlannedTemporalMutation]] = []
        seen_event_ids: set[str] = set()
        missing_events: list[str] = []
        skipped_missing_entities: list[str] = []

        for event_slug, mutation in MUTATION_ALIASES.items():
            event = self._event_repository.get_by_slug(event_slug)
            if event is None:
                missing_events.append(event_slug)
                continue
            if event.id in seen_event_ids:
                continue
            seen_event_ids.add(event.id)
            self._append_character_update_plans(
                plans,
                skipped_missing_entities,
                event=event,
                characters_by_slug=characters_by_slug,
                planets_by_slug=planets_by_slug,
                mutation=mutation,
            )
            self._append_control_update_plans(
                plans,
                skipped_missing_entities,
                event=event,
                planets_by_slug=planets_by_slug,
                factions_by_slug=factions_by_slug,
                mutation=mutation,
            )
            self._append_artifact_update_plans(
                plans,
                skipped_missing_entities,
                event=event,
                characters_by_slug=characters_by_slug,
                planets_by_slug=planets_by_slug,
                mutation=mutation,
            )

        return plans, missing_events, skipped_missing_entities

    def _append_character_update_plans(
        self,
        plans: list[tuple[Event, PlannedTemporalMutation]],
        skipped_missing_entities: list[str],
        *,
        event: Event,
        characters_by_slug: Mapping[str, Character],
        planets_by_slug: Mapping[str, Planet],
        mutation: EventStateMutation,
    ) -> None:
        for character_slug, update in mutation.character_updates.items():
            character = self._resolve_character(characters_by_slug, character_slug)
            if character is None:
                skipped_missing_entities.append(
                    f"{event.slug}: character slug not found: {character_slug}"
                )
                continue
            if update.is_alive is not None:
                plans.append(
                    (
                        event,
                        PlannedTemporalMutation(
                            event_slug=event.slug,
                            relationship_type=RelationshipType.SETS_ALIVE_STATE,
                            to_node_id=character.id,
                            value_bool=update.is_alive,
                            note=self._backfill_note(event.slug),
                        ),
                    )
                )
            if update.location_planet_slug is None:
                continue
            planet = planets_by_slug.get(update.location_planet_slug)
            if planet is None:
                skipped_missing_entities.append(
                    f"{event.slug}: planet slug not found: {update.location_planet_slug}"
                )
                continue
            plans.append(
                (
                    event,
                    PlannedTemporalMutation(
                        event_slug=event.slug,
                        relationship_type=RelationshipType.SETS_CHARACTER_LOCATION,
                        to_node_id=planet.id,
                        subject_node_id=character.id,
                        note=self._backfill_note(event.slug),
                    ),
                )
            )

    def _append_control_update_plans(
        self,
        plans: list[tuple[Event, PlannedTemporalMutation]],
        skipped_missing_entities: list[str],
        *,
        event: Event,
        planets_by_slug: Mapping[str, Planet],
        factions_by_slug: Mapping[str, Faction],
        mutation: EventStateMutation,
    ) -> None:
        for planet_slug, faction_slug in mutation.control_updates.items():
            planet = planets_by_slug.get(planet_slug)
            faction = factions_by_slug.get(faction_slug)
            if planet is None:
                skipped_missing_entities.append(
                    f"{event.slug}: planet slug not found: {planet_slug}"
                )
                continue
            if faction is None:
                skipped_missing_entities.append(
                    f"{event.slug}: faction slug not found: {faction_slug}"
                )
                continue
            plans.append(
                (
                    event,
                    PlannedTemporalMutation(
                        event_slug=event.slug,
                        relationship_type=RelationshipType.SETS_PLANET_CONTROL,
                        to_node_id=faction.id,
                        subject_node_id=planet.id,
                        note=self._backfill_note(event.slug),
                    ),
                )
            )

    def _append_artifact_update_plans(
        self,
        plans: list[tuple[Event, PlannedTemporalMutation]],
        skipped_missing_entities: list[str],
        *,
        event: Event,
        characters_by_slug: Mapping[str, Character],
        planets_by_slug: Mapping[str, Planet],
        mutation: EventStateMutation,
    ) -> None:
        for artifact_key, update in mutation.artifact_updates.items():
            to_node_id = self._resolve_artifact_target_id(
                event_slug=event.slug,
                artifact_key=artifact_key,
                update=update,
                characters_by_slug=characters_by_slug,
                planets_by_slug=planets_by_slug,
                skipped_missing_entities=skipped_missing_entities,
            )
            if to_node_id is None:
                continue
            plans.append(
                (
                    event,
                    PlannedTemporalMutation(
                        event_slug=event.slug,
                        relationship_type=RelationshipType.SETS_ARTIFACT_LOCATION,
                        to_node_id=to_node_id,
                        artifact_key=artifact_key,
                        note=update.note or self._backfill_note(event.slug),
                    ),
                )
            )

    def _resolve_artifact_target_id(
        self,
        *,
        event_slug: str,
        artifact_key: str,
        update: ArtifactMutation,
        characters_by_slug: Mapping[str, Character],
        planets_by_slug: Mapping[str, Planet],
        skipped_missing_entities: list[str],
    ) -> str | None:
        if update.holder_character_slug is not None:
            holder = self._resolve_character(characters_by_slug, update.holder_character_slug)
            if holder is None:
                skipped_missing_entities.append(
                    f"{event_slug}: character slug not found: {update.holder_character_slug}"
                )
                return None
            return holder.id
        if update.location_planet_slug is not None:
            planet = planets_by_slug.get(update.location_planet_slug)
            if planet is None:
                skipped_missing_entities.append(
                    f"{event_slug}: planet slug not found: {update.location_planet_slug}"
                )
                return None
            return planet.id
        skipped_missing_entities.append(
            f"{event_slug}: artifact mutation {artifact_key} has no holder or location"
        )
        return None

    @staticmethod
    def _backfill_note(event_slug: str) -> str:
        return f"Backfilled from curated catalog for {event_slug}."

    @staticmethod
    def _describe(event_slug: str, plan: PlannedTemporalMutation) -> str:
        parts = [event_slug, plan.relationship_type.value, plan.to_node_id]
        if plan.subject_node_id is not None:
            parts.append(f"subject={plan.subject_node_id}")
        if plan.artifact_key is not None:
            parts.append(f"artifact={plan.artifact_key}")
        if plan.value_bool is not None:
            parts.append(f"value_bool={plan.value_bool}")
        return " | ".join(parts)

    @staticmethod
    def _resolve_character(
        characters_by_slug: Mapping[str, Character], character_slug: str
    ) -> Character | None:
        for candidate_slug in CHARACTER_SLUG_ALIASES.get(character_slug, (character_slug,)):
            character = characters_by_slug.get(candidate_slug)
            if character is not None:
                return character
        return None
