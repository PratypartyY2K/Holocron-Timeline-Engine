from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
