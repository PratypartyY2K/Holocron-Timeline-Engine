from collections.abc import Iterator
from uuid import uuid4

import pytest
from neo4j import Driver, GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from app.core.config import Settings


def _integration_settings() -> Settings:
    return Settings(
        NEO4J_URI="bolt://localhost:7687",
        NEO4J_USERNAME="neo4j",
        NEO4J_PASSWORD="changeme123",
        NEO4J_DATABASE="neo4j",
    )


@pytest.fixture(scope="session")
def integration_settings() -> Settings:
    return _integration_settings()


@pytest.fixture(scope="session")
def neo4j_driver(integration_settings: Settings) -> Iterator[Driver]:
    driver = GraphDatabase.driver(
        integration_settings.neo4j_uri,
        auth=(integration_settings.neo4j_username, integration_settings.neo4j_password),
    )
    try:
        driver.verify_connectivity()
    except (OSError, ServiceUnavailable, Neo4jError) as exc:
        driver.close()
        pytest.skip(
            f"Neo4j integration tests require a local database at {integration_settings.neo4j_uri}: {exc}"
        )
    try:
        yield driver
    finally:
        driver.close()


@pytest.fixture()
def integration_namespace(neo4j_driver: Driver, integration_settings: Settings) -> Iterator[str]:
    namespace = f"it-{uuid4()}"
    try:
        yield namespace
    finally:
        query = """
        MATCH (n)
        WHERE n.id STARTS WITH $namespace
        DETACH DELETE n
        """
        with neo4j_driver.session(database=integration_settings.neo4j_database) as session:
            session.run(query, namespace=namespace).consume()
