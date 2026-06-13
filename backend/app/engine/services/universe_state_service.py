from app.domain.entities.event import Event
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


class UniverseStateService:
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

    def get_state_before_event(self, event_id: str) -> UniverseState:
        focus_event = self._event_repository.get_by_id(event_id)
        if focus_event is None:
            raise EntityNotFoundError(f"Event not found: {event_id}")

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
        prior_events = [item for item in events if self._sort_key(item) < self._sort_key(focus_event)]

        all_planets = self._planet_repository.list_planets()
        planets_by_slug = {planet.slug: planet for planet in all_planets}
        planets_by_id = {planet.id: planet for planet in all_planets}
        all_factions = self._faction_repository.list_factions()
        factions_by_slug = {faction.slug: faction for faction in all_factions}
        factions_by_id = {faction.id: faction for faction in all_factions}
        all_characters = self._character_repository.list_characters()
        characters_by_id = {character.id: character for character in all_characters}
        tracked_characters = {character.slug: character for character in all_characters if character.slug in TRACKED_CHARACTER_SLUGS}

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

        graph_mutations = self._graph_repository.list_state_mutations_before_event(event_id=event_id)
        for mutation in graph_mutations:
            if mutation.type is RelationshipType.SETS_ALIVE_STATE:
                character = characters_by_id.get(mutation.to_node_id)
                state = None if character is None else character_states.get(character.slug)
                if state is not None and mutation.value_bool is not None:
                    state.is_alive = mutation.value_bool

            elif mutation.type is RelationshipType.SETS_CHARACTER_LOCATION:
                if mutation.subject_node_id is None:
                    continue
                character = characters_by_id.get(mutation.subject_node_id)
                planet = planets_by_id.get(mutation.to_node_id)
                state = None if character is None else character_states.get(character.slug)
                if state is not None and planet is not None:
                    state.location_planet_slug = planet.slug
                    state.location_planet_name = planet.name

            elif mutation.type is RelationshipType.SETS_PLANET_CONTROL:
                if mutation.subject_node_id is None:
                    continue
                planet = planets_by_id.get(mutation.subject_node_id)
                faction = factions_by_id.get(mutation.to_node_id)
                if planet is None or faction is None:
                    continue
                faction_control[planet.slug] = FactionControlState(
                    planet_slug=planet.slug,
                    planet_name=planet.name,
                    faction_slug=faction.slug,
                    faction_name=faction.name,
                )

            elif mutation.type is RelationshipType.SETS_ARTIFACT_LOCATION:
                if mutation.artifact_key is None:
                    continue
                artifact = artifacts.get(mutation.artifact_key)
                if artifact is None:
                    artifact = ArtifactLocationState(
                        artifact_key=mutation.artifact_key,
                        artifact_name=ARTIFACT_NAMES.get(mutation.artifact_key, mutation.artifact_key),
                    )
                    artifacts[mutation.artifact_key] = artifact
                holder = characters_by_id.get(mutation.to_node_id)
                planet = planets_by_id.get(mutation.to_node_id)
                artifact.holder_character_slug = holder.slug if holder is not None else None
                artifact.holder_character_name = holder.name if holder is not None else None
                artifact.location_planet_slug = planet.slug if planet is not None else None
                artifact.location_planet_name = planet.name if planet is not None else None
                artifact.note = mutation.note or mutation.value_text

        return UniverseState(
            event_id=focus_event.id,
            event_slug=focus_event.slug,
            event_title=focus_event.title,
            as_of_year=focus_event.start_year,
            prior_event_count=len(prior_events),
            projection_mode="graph-event-projection",
            notes=list(PROJECTION_NOTES),
            characters=sorted(character_states.values(), key=lambda item: item.name),
            faction_control=sorted(faction_control.values(), key=lambda item: item.planet_name),
            artifacts=sorted(artifacts.values(), key=lambda item: item.artifact_name),
        )

    @staticmethod
    def _sort_key(event: Event) -> tuple[int, str, str]:
        return (event.start_year, event.title.casefold(), event.id)
