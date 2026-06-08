from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.domain.errors import (
    ChronologyError,
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    UnsupportedRelationshipError,
    ValidationError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(EntityNotFoundError)
    async def handle_not_found(_, exc: EntityNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(DuplicateEntityError)
    async def handle_duplicate(_, exc: DuplicateEntityError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(UnsupportedRelationshipError)
    async def handle_unsupported(_, exc: UnsupportedRelationshipError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    @app.exception_handler(ChronologyError)
    async def handle_validation(_, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
