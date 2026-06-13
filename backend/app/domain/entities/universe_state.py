from dataclasses import dataclass, field


@dataclass(slots=True)
class UniverseCharacterState:
    id: str
    slug: str
    name: str
    is_alive: bool
    location_planet_slug: str | None = None
    location_planet_name: str | None = None


@dataclass(slots=True)
class FactionControlState:
    planet_slug: str
    planet_name: str
    faction_slug: str
    faction_name: str


@dataclass(slots=True)
class ArtifactLocationState:
    artifact_key: str
    artifact_name: str
    holder_character_slug: str | None = None
    holder_character_name: str | None = None
    location_planet_slug: str | None = None
    location_planet_name: str | None = None
    note: str | None = None


@dataclass(slots=True)
class UniverseState:
    event_id: str
    event_slug: str
    event_title: str
    as_of_year: int
    prior_event_count: int
    projection_mode: str
    notes: list[str] = field(default_factory=list)
    characters: list[UniverseCharacterState] = field(default_factory=list)
    faction_control: list[FactionControlState] = field(default_factory=list)
    artifacts: list[ArtifactLocationState] = field(default_factory=list)
