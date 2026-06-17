from __future__ import annotations

import logging
from time import perf_counter
from typing import TypeVar


T = TypeVar("T")


class Neo4jQueryMonitor:
    def __init__(self, *, slow_query_threshold_ms: float, logger: logging.Logger | None = None) -> None:
        self._slow_query_threshold_ms = slow_query_threshold_ms
        self._logger = logger or logging.getLogger("app.observability.neo4j")

    def measure(self, *, query_name: str, operation) -> T:
        started_at = perf_counter()
        try:
            result = operation()
        except Exception:
            duration_ms = (perf_counter() - started_at) * 1000
            self._logger.exception(
                "neo4j_query_failed query_name=%s duration_ms=%.2f",
                query_name,
                duration_ms,
            )
            raise

        duration_ms = (perf_counter() - started_at) * 1000
        if duration_ms >= self._slow_query_threshold_ms:
            self._logger.warning(
                "neo4j_query_slow query_name=%s duration_ms=%.2f threshold_ms=%.2f",
                query_name,
                duration_ms,
                self._slow_query_threshold_ms,
            )
        else:
            self._logger.debug(
                "neo4j_query_completed query_name=%s duration_ms=%.2f",
                query_name,
                duration_ms,
            )
        return result
