from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CharacterMutation:
    is_alive: bool | None = None
    location_planet_slug: str | None = None


@dataclass(frozen=True, slots=True)
class ArtifactMutation:
    holder_character_slug: str | None = None
    location_planet_slug: str | None = None
    note: str | None = None


@dataclass(frozen=True, slots=True)
class EventStateMutation:
    character_updates: dict[str, CharacterMutation] = field(default_factory=dict)
    control_updates: dict[str, str] = field(default_factory=dict)
    artifact_updates: dict[str, ArtifactMutation] = field(default_factory=dict)


TRACKED_CHARACTER_SLUGS: tuple[str, ...] = (
    "luke-skywalker",
    "leia-organa",
    "grand-moff-tarkin",
    "wilhuff-tarkin",
    "sheev-palpatine",
)

CHARACTER_SLUG_ALIASES: dict[str, tuple[str, ...]] = {
    "grand-moff-tarkin": ("grand-moff-tarkin", "wilhuff-tarkin"),
}

BASELINE_CHARACTER_LOCATIONS: dict[str, str] = {
    "sheev-palpatine": "coruscant",
}

BASELINE_PLANET_CONTROL: dict[str, str] = {
    "alderaan": "galactic-republic",
    "coruscant": "galactic-republic",
    "geonosis": "cis",
    "naboo": "galactic-republic",
}

BASELINE_ARTIFACTS: dict[str, ArtifactMutation] = {
    "skywalker-lightsaber": ArtifactMutation(
        holder_character_slug="luke-skywalker",
        location_planet_slug=None,
        note="Tracked as Luke Skywalker's inherited lightsaber entering the Yavin campaign.",
    ),
}

ARTIFACT_NAMES: dict[str, str] = {
    "skywalker-lightsaber": "Skywalker lightsaber",
}

MUTATION_ALIASES: dict[str, EventStateMutation] = {
    "rise-of-the-empire": EventStateMutation(
        control_updates={
            "alderaan": "galactic-empire",
            "coruscant": "galactic-empire",
            "naboo": "galactic-empire",
        }
    ),
    "battle-of-yavin": EventStateMutation(
        character_updates={
            "grand-moff-tarkin": CharacterMutation(is_alive=False),
        }
    ),
    "battle-of-crait": EventStateMutation(
        character_updates={
            "luke-skywalker": CharacterMutation(is_alive=False),
        }
    ),
    "battle-of-exegol": EventStateMutation(
        character_updates={
            "sheev-palpatine": CharacterMutation(is_alive=False),
        }
    ),
}

PROJECTION_NOTES: tuple[str, ...] = (
    "Snapshot is computed from graph-authored temporal mutations that happened strictly before the focus event.",
    "Seeded baseline facts are used only as the starting state for tracked entities, systems, and artifacts.",
    "Events in the same start year are ordered deterministically by title and id before mutations are applied.",
)
