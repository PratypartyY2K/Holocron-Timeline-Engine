from fastapi import APIRouter

from app.api.routes.characters import router as characters_router
from app.api.routes.engine import router as engine_router
from app.api.routes.events import router as events_router
from app.api.routes.factions import router as factions_router
from app.api.routes.graph import router as graph_router
from app.api.routes.health import router as health_router
from app.api.routes.planets import router as planets_router
from app.api.routes.search import router as search_router
from app.api.routes.timeline import router as timeline_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(search_router, prefix="/search", tags=["search"])
api_router.include_router(characters_router, prefix="/characters", tags=["characters"])
api_router.include_router(engine_router, prefix="/engine", tags=["engine"])
api_router.include_router(events_router, prefix="/events", tags=["events"])
api_router.include_router(planets_router, prefix="/planets", tags=["planets"])
api_router.include_router(factions_router, prefix="/factions", tags=["factions"])
api_router.include_router(timeline_router, prefix="/timeline", tags=["timeline"])
api_router.include_router(graph_router, prefix="/graph", tags=["graph"])
