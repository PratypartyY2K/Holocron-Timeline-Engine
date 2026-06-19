from app.scripts.neo4j_uri import normalize_neo4j_uri_to_localhost, normalize_runtime_neo4j_uri


def test_normalize_neo4j_uri_to_localhost_rewrites_docker_hostname() -> None:
    assert normalize_neo4j_uri_to_localhost("bolt://neo4j:7687") == "bolt://localhost:7687"


def test_normalize_runtime_neo4j_uri_rewrites_to_localhost_outside_container(monkeypatch) -> None:
    monkeypatch.setattr("app.scripts.neo4j_uri._is_running_in_container", lambda: False)

    assert normalize_runtime_neo4j_uri("bolt://neo4j:7687") == "bolt://localhost:7687"


def test_normalize_runtime_neo4j_uri_preserves_docker_hostname_inside_container(
    monkeypatch,
) -> None:
    monkeypatch.setattr("app.scripts.neo4j_uri._is_running_in_container", lambda: True)

    assert normalize_runtime_neo4j_uri("bolt://neo4j:7687") == "bolt://neo4j:7687"
