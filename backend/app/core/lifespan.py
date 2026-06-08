from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.neo4j import close_driver, init_driver


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_driver()
    yield
    close_driver()

