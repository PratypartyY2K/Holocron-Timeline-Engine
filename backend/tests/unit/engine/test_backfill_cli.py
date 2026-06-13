from app.scripts.neo4j_uri import normalize_cli_neo4j_uri


def test_normalize_cli_neo4j_uri_rewrites_docker_service_hostname() -> None:
    assert normalize_cli_neo4j_uri("bolt://neo4j:7687") == "bolt://localhost:7687"


def test_normalize_cli_neo4j_uri_leaves_other_hosts_unchanged() -> None:
    assert normalize_cli_neo4j_uri("bolt://localhost:7687") == "bolt://localhost:7687"
