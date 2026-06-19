from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from threading import RLock

from app.domain.entities.character import Character
from app.domain.entities.event import Event
from app.domain.entities.faction import Faction
from app.domain.entities.planet import Planet
from app.domain.entities.relationship import Relationship
from app.domain.entities.universe_state import (
    ArtifactLocationState,
    FactionControlState,
    UniverseCharacterState,
    UniverseState,
)
from app.domain.enums import RelationshipType
from app.domain.errors import EntityNotFoundError
from app.engine.universe_state_catalog import (
    ARTIFACT_NAMES,
    BASELINE_ARTIFACTS,
    BASELINE_CHARACTER_LOCATIONS,
    BASELINE_PLANET_CONTROL,
    PROJECTION_NOTES,
    TRACKED_CHARACTER_SLUGS,
)
from app.repositories.interfaces.character_repository import CharacterRepository
from app.repositories.interfaces.event_repository import EventRepository
from app.repositories.interfaces.faction_repository import FactionRepository
from app.repositories.interfaces.graph_repository import GraphRepository
from app.repositories.interfaces.planet_repository import PlanetRepository


@dataclass(slots=True)
class _ProjectionState:
    characters: dict[str, UniverseCharacterState] = field(default_factory=dict)
    faction_control: dict[str, FactionControlState] = field(default_factory=dict)
    artifacts: dict[str, ArtifactLocationState] = field(default_factory=dict)


@dataclass(slots=True)
class _ProjectionCache:
    events_by_id: dict[str, Event]
    sorted_events: list[Event]
    characters_by_id: dict[str, Character]
    planets_by_id: dict[str, Planet]
    factions_by_id: dict[str, Faction]
    mutations_by_event_id: dict[str, list[Relationship]]
    checkpoints: list[tuple[tuple[int, str, str], str, _ProjectionState]]
    base_state: _ProjectionState


class UniverseStateService:
    _projection_cache: _ProjectionCache | None = None
    _projection_cache_lock = RLock()

    def __init__(
        self,
        *,
        event_repository: EventRepository,
        character_repository: CharacterRepository,
        planet_repository: PlanetRepository,
        faction_repository: FactionRepository,
        graph_repository: GraphRepository,
    ) -> None:
        self._event_repository = event_repository
        self._character_repository = character_repository
        self._planet_repository = planet_repository
        self._faction_repository = faction_repository
        self._graph_repository = graph_repository

    @classmethod
    def invalidate_projection_cache(cls) -> None:
        with cls._projection_cache_lock:
            cls._projection_cache = None

    def get_state_before_event(self, event_id: str) -> UniverseState:
        projection_cache = self._get_or_build_projection_cache()
        focus_event = projection_cache.events_by_id.get(event_id)
        if focus_event is None:
            raise EntityNotFoundError(f"Event not found: {event_id}")

        projection_state = self._state_before_event(projection_cache, focus_event)

        return UniverseState(
            event_id=focus_event.id,
            event_slug=focus_event.slug,
            event_title=focus_event.title,
            as_of_year=focus_event.start_year,
            prior_event_count=self._count_prior_events(projection_cache.sorted_events, focus_event),
            projection_mode="graph-event-projection",
            notes=list(PROJECTION_NOTES),
            characters=sorted(projection_state.characters.values(), key=lambda item: item.name),
            faction_control=sorted(
                projection_state.faction_control.values(), key=lambda item: item.planet_name
            ),
            artifacts=sorted(
                projection_state.artifacts.values(), key=lambda item: item.artifact_name
            ),
        )

    @staticmethod
    def _sort_key(event: Event) -> tuple[int, str, str]:
        return (event.start_year, event.title.casefold(), event.id)

    def _get_or_build_projection_cache(self) -> _ProjectionCache:
        cache_cls = type(self)
        with cache_cls._projection_cache_lock:
            if cache_cls._projection_cache is None:
                cache_cls._projection_cache = self._build_projection_cache()
            return cache_cls._projection_cache

    def _build_projection_cache(self) -> _ProjectionCache:
        events, _ = self._event_repository.list_events(
            start_year=None,
            end_year=None,
            era=None,
            character=None,
            location=None,
            causal_depth=None,
            limit=5_000,
            offset=0,
            order="asc",
        )
        sorted_events = sorted(events, key=self._sort_key)
        events_by_id = {event.id: event for event in sorted_events}

        all_planets = self._planet_repository.list_planets()
        planets_by_slug = {planet.slug: planet for planet in all_planets}
        planets_by_id = {planet.id: planet for planet in all_planets}
        all_factions = self._faction_repository.list_factions()
        factions_by_slug = {faction.slug: faction for faction in all_factions}
        factions_by_id = {faction.id: faction for faction in all_factions}
        all_characters = self._character_repository.list_characters()
        characters_by_id = {character.id: character for character in all_characters}
        tracked_characters = {
            character.slug: character
            for character in all_characters
            if character.slug in TRACKED_CHARACTER_SLUGS
        }

        base_state = self._build_base_state(
            tracked_characters=tracked_characters,
            planets_by_slug=planets_by_slug,
            factions_by_slug=factions_by_slug,
        )

        all_mutations = []
        if sorted_events:
            latest_event = sorted_events[-1]
            all_mutations = self._graph_repository.list_state_mutations_before_event(
                event_id=latest_event.id
            )

        mutations_by_event_id: dict[str, list[Relationship]] = {}
        for mutation in all_mutations:
            mutations_by_event_id.setdefault(mutation.from_node_id, []).append(mutation)

        state_after_event = deepcopy(base_state)
        checkpoints: list[tuple[tuple[int, str, str], str, _ProjectionState]] = []
        for index, event in enumerate(sorted_events):
            self._apply_event_mutations(
                state_after_event,
                mutations_by_event_id.get(event.id, []),
                characters_by_id=characters_by_id,
                planets_by_id=planets_by_id,
                factions_by_id=factions_by_id,
            )
            next_event = sorted_events[index + 1] if index + 1 < len(sorted_events) else None
            if next_event is None or next_event.era != event.era:
                checkpoints.append((self._sort_key(event), event.id, deepcopy(state_after_event)))

        return _ProjectionCache(
            events_by_id=events_by_id,
            sorted_events=sorted_events,
            characters_by_id=characters_by_id,
            planets_by_id=planets_by_id,
            factions_by_id=factions_by_id,
            mutations_by_event_id=mutations_by_event_id,
            checkpoints=checkpoints,
            base_state=base_state,
        )

    def _state_before_event(self, cache: _ProjectionCache, focus_event: Event) -> _ProjectionState:
        focus_key = self._sort_key(focus_event)
        prior_checkpoint_event_id: str | None = None
        state = deepcopy(cache.base_state)
        for checkpoint_key, checkpoint_event_id, checkpoint_state in cache.checkpoints:
            if checkpoint_key < focus_key:
                prior_checkpoint_event_id = checkpoint_event_id
                state = deepcopy(checkpoint_state)
            else:
                break

        start_replay = prior_checkpoint_event_id is None
        for event in cache.sorted_events:
            if not start_replay:
                if event.id == prior_checkpoint_event_id:
                    start_replay = True
                continue
            if self._sort_key(event) >= focus_key:
                break
            self._apply_event_mutations(
                state,
                cache.mutations_by_event_id.get(event.id, []),
                characters_by_id=cache.characters_by_id,
                planets_by_id=cache.planets_by_id,
                factions_by_id=cache.factions_by_id,
            )
        return state

    @staticmethod
    def _count_prior_events(sorted_events: list[Event], focus_event: Event) -> int:
        focus_key = UniverseStateService._sort_key(focus_event)
        return sum(
            1 for event in sorted_events if UniverseStateService._sort_key(event) < focus_key
        )

    @staticmethod
    def _build_base_state(
        *,
        tracked_characters: Mapping[str, Character],
        planets_by_slug: Mapping[str, Planet],
        factions_by_slug: Mapping[str, Faction],
    ) -> _ProjectionState:
        character_states = {
            slug: UniverseCharacterState(
                id=character.id,
                slug=character.slug,
                name=character.name,
                is_alive=True,
                location_planet_slug=BASELINE_CHARACTER_LOCATIONS.get(slug),
                location_planet_name=(
                    planets_by_slug[BASELINE_CHARACTER_LOCATIONS[slug]].name
                    if BASELINE_CHARACTER_LOCATIONS.get(slug) in planets_by_slug
                    else None
                ),
            )
            for slug, character in tracked_characters.items()
        }

        faction_control = {}
        for planet_slug, faction_slug in BASELINE_PLANET_CONTROL.items():
            planet = planets_by_slug.get(planet_slug)
            faction = factions_by_slug.get(faction_slug)
            if planet is None or faction is None:
                continue
            faction_control[planet_slug] = FactionControlState(
                planet_slug=planet.slug,
                planet_name=planet.name,
                faction_slug=faction.slug,
                faction_name=faction.name,
            )

        artifacts = {}
        for artifact_key, baseline in BASELINE_ARTIFACTS.items():
            holder = tracked_characters.get(baseline.holder_character_slug or "")
            planet = planets_by_slug.get(baseline.location_planet_slug or "")
            artifacts[artifact_key] = ArtifactLocationState(
                artifact_key=artifact_key,
                artifact_name=ARTIFACT_NAMES.get(artifact_key, artifact_key),
                holder_character_slug=holder.slug if holder is not None else None,
                holder_character_name=holder.name if holder is not None else None,
                location_planet_slug=planet.slug if planet is not None else None,
                location_planet_name=planet.name if planet is not None else None,
                note=baseline.note,
            )

        return _ProjectionState(
            characters=character_states,
            faction_control=faction_control,
            artifacts=artifacts,
        )

    @staticmethod
    def _apply_event_mutations(
        state: _ProjectionState,
        mutations: list[Relationship],
        *,
        characters_by_id: Mapping[str, Character],
        planets_by_id: Mapping[str, Planet],
        factions_by_id: Mapping[str, Faction],
    ) -> None:
        for mutation in mutations:
            if mutation.type is RelationshipType.SETS_ALIVE_STATE:
                character = characters_by_id.get(mutation.to_node_id)
                state_item = None if character is None else state.characters.get(character.slug)
                if state_item is not None and mutation.value_bool is not None:
                    state_item.is_alive = mutation.value_bool

            elif mutation.type is RelationshipType.SETS_CHARACTER_LOCATION:
                if mutation.subject_node_id is None:
                    continue
                character = characters_by_id.get(mutation.subject_node_id)
                planet = planets_by_id.get(mutation.to_node_id)
                state_item = None if character is None else state.characters.get(character.slug)
                if state_item is not None and planet is not None:
                    state_item.location_planet_slug = planet.slug
                    state_item.location_planet_name = planet.name

            elif mutation.type is RelationshipType.SETS_PLANET_CONTROL:
                if mutation.subject_node_id is None:
                    continue
                planet = planets_by_id.get(mutation.subject_node_id)
                faction = factions_by_id.get(mutation.to_node_id)
                if planet is None or faction is None:
                    continue
                state.faction_control[planet.slug] = FactionControlState(
                    planet_slug=planet.slug,
                    planet_name=planet.name,
                    faction_slug=faction.slug,
                    faction_name=faction.name,
                )

            elif mutation.type is RelationshipType.SETS_ARTIFACT_LOCATION:
                if mutation.artifact_key is None:
                    continue
                artifact = state.artifacts.get(mutation.artifact_key)
                if artifact is None:
                    artifact = ArtifactLocationState(
                        artifact_key=mutation.artifact_key,
                        artifact_name=ARTIFACT_NAMES.get(
                            mutation.artifact_key, mutation.artifact_key
                        ),
                    )
                    state.artifacts[mutation.artifact_key] = artifact
                holder = characters_by_id.get(mutation.to_node_id)
                planet = planets_by_id.get(mutation.to_node_id)
                artifact.holder_character_slug = holder.slug if holder is not None else None
                artifact.holder_character_name = holder.name if holder is not None else None
                artifact.location_planet_slug = planet.slug if planet is not None else None
                artifact.location_planet_name = planet.name if planet is not None else None
                artifact.note = mutation.note or mutation.value_text
