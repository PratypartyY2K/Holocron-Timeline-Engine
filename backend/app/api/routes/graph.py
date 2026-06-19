from fastapi import APIRouter, Depends, status

from app.api.dependencies.services import get_relationship_service
from app.engine.dto import CreateRelationshipCommand
from app.engine.services.relationship_service import RelationshipService
from app.schemas.graph import CreateRelationshipRequest, RelationshipResponse

router = APIRouter()


@router.post(
    "/relationships", response_model=RelationshipResponse, status_code=status.HTTP_201_CREATED
)
def create_relationship(
    request: CreateRelationshipRequest,
    service: RelationshipService = Depends(get_relationship_service),
) -> RelationshipResponse:
    relationship = service.create_relationship(
        CreateRelationshipCommand(
            type=request.type,
            from_node_id=request.from_node_id,
            to_node_id=request.to_node_id,
            note=request.note,
            subject_node_id=request.subject_node_id,
            artifact_key=request.artifact_key,
            value_bool=request.value_bool,
            value_text=request.value_text,
        )
    )
    return RelationshipResponse.model_validate(relationship)
