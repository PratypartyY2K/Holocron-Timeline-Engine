# Holocron Timeline Engine

Holocron Timeline Engine is a Star Wars timeline explorer and knowledge graph built with a Next.js frontend, a FastAPI backend, and Neo4j for graph storage. It focuses on event chronology, causal relationships, and "what if" timeline break simulations.

## What It Is

- Interactive archive for events, characters, planets, and factions
- Event-centric graph explorer with dependency and consequence traversal
- Timeline simulator that shows how downstream events change when a causal event is broken
- Universe-state projection system that reconstructs character, faction, and artifact state before a selected event

## Key Features

- Chronology-aware event timeline with filters for era, character, location, order, and date range
- Slug-based detail pages for events, characters, planets, and factions
- Causal graph views for event dependencies, consequences, and alternate simulated branches
- Search across events, characters, planets, and factions
- Relationship authoring API for graph edges and temporal mutations
- Curated mutation backfill pipeline for restoring timeline state into Neo4j

## Engineering Highlights

- Graph-based data model using Neo4j
- Causal dependency traversal implemented with Cypher queries
- Topological propagation for timeline break simulation
- Separation of engine logic from the API layer
- Typed API layer built with FastAPI and Pydantic

## Demo Routes

- `/` search-driven homepage and archive entry point
- `/events` main timeline explorer
- `/events/[slug]` event detail page with causal graph, impact, what-if simulation, and universe state
- `/characters` character index
- `/characters/[slug]` character detail page
- `/planets` planet index
- `/planets/[slug]` planet detail page
- `/factions` faction index
- `/factions/[slug]` faction detail page

Examples:

- `http://localhost:3000/`
- `http://localhost:3000/events`
- `http://localhost:3000/events/battle-of-yavin?depth=2`
- `http://localhost:3000/characters/luke-skywalker`

## Example Use Case

1. Open `/events`.
2. Select `Battle of Yavin`.
3. View its causal graph.
4. Toggle `What If?`.
5. Observe downstream events become invalidated or unresolved.

This demonstrates how causal relationships propagate through the system when a key event is broken.

## Architecture

At a high level:

- `frontend/` contains the Next.js app and graph/timeline UI
- `backend/app/api/` exposes the FastAPI HTTP routes
- `backend/app/engine/` contains business logic for events, simulation, search, relationships, and universe state
- `backend/app/repositories/neo4j/` translates engine operations into Cypher queries
- `backend/app/domain/` defines the core entities and enums
- `backend/app/ingestion/` and `scripts/` support dataset transformation and import workflows

Request flow:

`Next.js UI -> FastAPI routes -> engine services -> repository interfaces -> Neo4j`

## Docs

- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Engineering Design](docs/engineering-design.md)

## Local Development

Run the full stack with Docker Compose:

```bash
docker compose -f docker/compose.yml up --build
```

Local endpoints:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`
- Neo4j Browser: `http://localhost:7474`

## Data Pipeline

Transform and ingest archive data:

```bash
uv run python scripts/transform.py
uv run python scripts/ingest.py
```

Backfill curated temporal mutations through backend validation:

```bash
cd backend
python -m app.scripts.backfill_temporal_mutations --dry-run
python -m app.scripts.backfill_temporal_mutations
```

## Testing

```bash
cd backend
pytest
```
