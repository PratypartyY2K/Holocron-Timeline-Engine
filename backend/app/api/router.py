from fastapi import APIRouter

from app.api.routes.events import router as events_router
from app.api.routes.graph import router as graph_router
from app.api.routes.health import router as health_router
from app.api.routes.timeline import router as timeline_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(events_router, prefix="/events", tags=["events"])
api_router.include_router(timeline_router, prefix="/timeline", tags=["timeline"])
api_router.include_router(graph_router, prefix="/graph", tags=["graph"])

