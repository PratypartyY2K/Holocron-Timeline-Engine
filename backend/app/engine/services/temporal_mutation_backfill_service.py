from dataclasses import dataclass
from app.domain.entities.event import Event
from app.domain.errors import DuplicateEntityError
from app.domain.enums import RelationshipType
from app.engine.dto import CreateRelationshipCommand
from app.engine.universe_state_catalog import CHARACTER_SLUG_ALIASES, MUTATION_ALIASES
from app.repositories.interfaces.character_repository import CharacterRepository
from app.repositories.interfaces.event_repository import EventRepository
from app.repositories.interfaces.faction_repository import FactionRepository
from app.repositories.interfaces.planet_repository import PlanetRepository
from app.engine.services.relationship_service import RelationshipService


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
        characters_by_slug = {item.slug: item for item in self._character_repository.list_characters()}
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
                                note=f"Backfilled from curated catalog for {event.slug}.",
                            ),
                        )
                    )
                if update.location_planet_slug is not None:
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
                                note=f"Backfilled from curated catalog for {event.slug}.",
                            ),
                        )
                    )

            for planet_slug, faction_slug in mutation.control_updates.items():
                planet = planets_by_slug.get(planet_slug)
                faction = factions_by_slug.get(faction_slug)
                if planet is None:
                    skipped_missing_entities.append(f"{event.slug}: planet slug not found: {planet_slug}")
                    continue
                if faction is None:
                    skipped_missing_entities.append(f"{event.slug}: faction slug not found: {faction_slug}")
                    continue
                plans.append(
                    (
                        event,
                        PlannedTemporalMutation(
                            event_slug=event.slug,
                            relationship_type=RelationshipType.SETS_PLANET_CONTROL,
                            to_node_id=faction.id,
                            subject_node_id=planet.id,
                            note=f"Backfilled from curated catalog for {event.slug}.",
                        ),
                    )
                )

            for artifact_key, update in mutation.artifact_updates.items():
                to_node_id: str
                if update.holder_character_slug is not None:
                    holder = self._resolve_character(characters_by_slug, update.holder_character_slug)
                    if holder is None:
                        skipped_missing_entities.append(
                            f"{event.slug}: character slug not found: {update.holder_character_slug}"
                        )
                        continue
                    to_node_id = holder.id
                elif update.location_planet_slug is not None:
                    planet = planets_by_slug.get(update.location_planet_slug)
                    if planet is None:
                        skipped_missing_entities.append(
                            f"{event.slug}: planet slug not found: {update.location_planet_slug}"
                        )
                        continue
                    to_node_id = planet.id
                else:
                    skipped_missing_entities.append(
                        f"{event.slug}: artifact mutation {artifact_key} has no holder or location"
                    )
                    continue
                plans.append(
                    (
                        event,
                        PlannedTemporalMutation(
                            event_slug=event.slug,
                            relationship_type=RelationshipType.SETS_ARTIFACT_LOCATION,
                            to_node_id=to_node_id,
                            artifact_key=artifact_key,
                            note=update.note or f"Backfilled from curated catalog for {event.slug}.",
                        ),
                    )
                )

        return plans, missing_events, skipped_missing_entities

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
    def _resolve_character(characters_by_slug: dict[str, object], character_slug: str) -> object | None:
        for candidate_slug in CHARACTER_SLUG_ALIASES.get(character_slug, (character_slug,)):
            character = characters_by_slug.get(candidate_slug)
            if character is not None:
                return character
        return None
