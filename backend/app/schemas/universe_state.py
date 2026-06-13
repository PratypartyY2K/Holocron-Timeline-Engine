from pydantic import BaseModel, ConfigDict


class UniverseCharacterStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    name: str
    is_alive: bool
    location_planet_slug: str | None
    location_planet_name: str | None


class FactionControlStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    planet_slug: str
    planet_name: str
    faction_slug: str
    faction_name: str


class ArtifactLocationStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    artifact_key: str
    artifact_name: str
    holder_character_slug: str | None
    holder_character_name: str | None
    location_planet_slug: str | None
    location_planet_name: str | None
    note: str | None


class UniverseStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    event_slug: str
    event_title: str
    as_of_year: int
    prior_event_count: int
    projection_mode: str
    notes: list[str]
    characters: list[UniverseCharacterStateResponse]
    faction_control: list[FactionControlStateResponse]
    artifacts: list[ArtifactLocationStateResponse]
