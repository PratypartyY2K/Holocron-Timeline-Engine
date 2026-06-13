from urllib.parse import urlsplit, urlunsplit


def normalize_cli_neo4j_uri(uri: str) -> str:
    parsed = urlsplit(uri)
    if parsed.hostname != "neo4j":
        return uri

    port = parsed.port or 7687
    credentials = ""
    if parsed.username is not None:
        credentials = parsed.username
        if parsed.password is not None:
            credentials = f"{credentials}:{parsed.password}"
        credentials = f"{credentials}@"

    normalized_netloc = f"{credentials}localhost:{port}"
    return urlunsplit((parsed.scheme, normalized_netloc, parsed.path, parsed.query, parsed.fragment))
