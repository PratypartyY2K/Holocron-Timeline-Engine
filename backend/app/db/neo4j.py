from neo4j import Driver, GraphDatabase

from app.core.config import get_settings
from app.scripts.neo4j_uri import normalize_runtime_neo4j_uri

_driver: Driver | None = None


def init_driver() -> Driver:
    global _driver
    if _driver is None:
        settings = get_settings()
        _driver = GraphDatabase.driver(
            normalize_runtime_neo4j_uri(settings.neo4j_uri),
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
    return _driver


def get_driver() -> Driver:
    if _driver is None:
        return init_driver()
    return _driver


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
