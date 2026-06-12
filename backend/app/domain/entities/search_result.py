from dataclasses import dataclass


@dataclass(slots=True)
class SearchResult:
    entity_type: str
    id: str
    slug: str
    label: str
    description: str | None
