from app.api.errors import register_exception_handlers
from app.api.router import api_router
from app.core.lifespan import lifespan
from app.core.logging import configure_logging
from app.core.config import get_settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


configure_logging()
settings = get_settings()

app = FastAPI(
    title="Holocron Timeline Engine API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")
register_exception_handlers(app)
