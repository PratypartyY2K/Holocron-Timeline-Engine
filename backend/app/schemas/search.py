from pydantic import BaseModel, ConfigDict


class SearchResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entity_type: str
    id: str
    slug: str
    label: str
    description: str | None
