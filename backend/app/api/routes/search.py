from fastapi import APIRouter, Depends, Query

from app.api.dependencies.services import get_search_service
from app.engine.services.search_service import SearchService
from app.schemas.search import SearchResultResponse

router = APIRouter()


@router.get("", response_model=list[SearchResultResponse])
def search(
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=25),
    service: SearchService = Depends(get_search_service),
) -> list[SearchResultResponse]:
    return [
        SearchResultResponse.model_validate(item) for item in service.search(query=q, limit=limit)
    ]
