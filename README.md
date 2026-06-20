# Holocron Timeline Engine

Holocron Timeline Engine is a graph-based system for modeling, exploring, and simulating causal timelines in fictional universes. Built with a Next.js frontend, a FastAPI backend, and Neo4j for graph storage, it helps users trace event dependencies, visualize causal relationships, simulate alternate timelines, and observe how changes propagate through a connected system.

## What It Is

- Graph-based timeline modeling system for causally linked events
- Interactive archive for events, characters, planets, and factions
- Alternate-timeline simulator for testing "what if" breaks in event chains
- Universe-state projection system for reconstructing character, faction, and artifact state before a selected event

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

## Performance Notes

- Deep dependency and consequence traversals become more expensive as the graph grows, because the backend assembles request-scoped subgraphs directly from Neo4j.
- Causal graph and simulation endpoints can produce larger payloads than simple entity lookups, especially when traversal depth or downstream fan-out increases.
- Timeline-break simulation cost grows with the size of the downstream subgraph, since the engine performs topological propagation over the affected branch rather than a constant-time lookup.

For deeper performance and scaling discussion, see [docs/architecture.md](docs/architecture.md).

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

### Documentation

- Architecture diagrams: HLD and LLD views in [docs/architecture.md](docs/architecture.md)
- Data model overview and relationship model in [docs/architecture.md](docs/architecture.md)
- System mechanics such as chronology normalization in [docs/architecture.md](docs/architecture.md)
- Example API and graph queries in [docs/api.md](docs/api.md) and [docs/architecture.md](docs/architecture.md)

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
