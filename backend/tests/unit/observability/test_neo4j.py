import logging
from time import sleep

import pytest

from app.observability.neo4j import Neo4jQueryMonitor


def test_neo4j_query_monitor_logs_debug_for_normal_query(caplog) -> None:
    monitor = Neo4jQueryMonitor(slow_query_threshold_ms=1000.0)

    with caplog.at_level(logging.DEBUG, logger="app.observability.neo4j"):
        result = monitor.measure(query_name="event.get_by_id", operation=lambda: {"ok": True})

    assert result == {"ok": True}
    assert "neo4j_query_completed" in caplog.text


def test_neo4j_query_monitor_logs_warning_for_slow_query(caplog) -> None:
    monitor = Neo4jQueryMonitor(slow_query_threshold_ms=0.01)

    def slow_operation() -> str:
        sleep(0.01)
        return "done"

    with caplog.at_level(logging.WARNING, logger="app.observability.neo4j"):
        result = monitor.measure(query_name="graph.search_entities", operation=slow_operation)

    assert result == "done"
    assert "neo4j_query_slow" in caplog.text


def test_neo4j_query_monitor_logs_failures(caplog) -> None:
    monitor = Neo4jQueryMonitor(slow_query_threshold_ms=1000.0)

    def failing_operation() -> None:
        raise RuntimeError("boom")

    with caplog.at_level(logging.ERROR, logger="app.observability.neo4j"):
        with pytest.raises(RuntimeError, match="boom"):
            monitor.measure(query_name="graph.create_relationship", operation=failing_operation)

    assert "neo4j_query_failed" in caplog.text
