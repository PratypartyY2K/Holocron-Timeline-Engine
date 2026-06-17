# Data Pipeline

Contributor-facing data lives under `data/raw/` as JSON fragments.

Transform raw fragments into one canonical dataset:

```bash
uv run python scripts/transform.py
```

Ingest the processed dataset into Neo4j through the backend services:

```bash
uv run python scripts/ingest.py
```

Each raw JSON file may contain any subset of:

```json
{
  "events": [],
  "characters": [],
  "planets": [],
  "factions": [],
  "relationships": []
}
```

Relationships use slug-based references:

```json
{
  "type": "INVOLVES",
  "source": {"type": "event", "slug": "battle-of-yavin"},
  "target": {"type": "character", "slug": "luke-skywalker"},
  "note": "Primary pilot"
}
```
