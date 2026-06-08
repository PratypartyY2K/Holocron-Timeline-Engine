from fastapi import APIRouter, Depends, status

from app.api.dependencies.services import get_planet_service
from app.engine.dto import CreatePlanetCommand
from app.engine.services.planet_service import PlanetService
from app.schemas.planets import CreatePlanetRequest, PlanetResponse

router = APIRouter()


@router.post("", response_model=PlanetResponse, status_code=status.HTTP_201_CREATED)
def create_planet(
    request: CreatePlanetRequest,
    service: PlanetService = Depends(get_planet_service),
) -> PlanetResponse:
    planet = service.create_planet(
        CreatePlanetCommand(
            slug=request.slug,
            name=request.name,
            description=request.description,
            region=request.region,
        )
    )
    return PlanetResponse.model_validate(planet)
