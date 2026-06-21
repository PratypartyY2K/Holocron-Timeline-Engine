from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from neo4j import Driver, Query

from app.core.config import Settings
from app.observability.neo4j import Neo4jQueryMonitor

T = TypeVar("T")


class Neo4jRepositoryBase:
    def __init__(self, driver: Driver, settings: Settings) -> None:
        self._driver = driver
        self._database = settings.neo4j_database
        self._query_timeout_seconds = settings.neo4j_query_timeout_seconds
        self._query_monitor = Neo4jQueryMonitor(
            slow_query_threshold_ms=settings.slow_query_threshold_ms,
            logger=logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}"),
        )

    def _measure_query(self, query_name: str, operation: Callable[[], T]) -> T:
        return self._query_monitor.measure(query_name=query_name, operation=operation)

    def _query(self, query: str) -> Query:
        return Query(query, timeout=self._query_timeout_seconds)

    def _run_single(self, *, query_name: str, query: str, **params: Any) -> Any:
        with self._driver.session(database=self._database) as session:
            return self._measure_query(
                query_name,
                lambda: session.run(self._query(query), **params).single(),
            )

    def _run_result(self, *, query_name: str, query: str, **params: Any) -> Any:
        with self._driver.session(database=self._database) as session:
            return self._measure_query(
                query_name,
                lambda: list(session.run(self._query(query), **params)),
            )

    def _execute_write(self, query_name: str, tx_fn: Callable[..., T], *args: Any) -> T:
        with self._driver.session(database=self._database) as session:
            return self._measure_query(query_name, lambda: session.execute_write(tx_fn, *args))
