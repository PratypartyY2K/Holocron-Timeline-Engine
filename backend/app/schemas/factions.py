from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from app.schemas.characters import CharacterResponse
from app.schemas.events import EventResponse


class CreateFactionRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)


class FactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class FactionDetailResponse(BaseModel):
    faction: FactionResponse
    characters: list[CharacterResponse]
    enemy_factions: list[FactionResponse]
    involved_events: list[EventResponse]
