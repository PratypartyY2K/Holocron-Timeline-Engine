# Holocron Timeline Engine

Holocron Timeline Engine is a graph-based system for modeling, exploring, and simulating causal timelines in fictional universes. Built with a Next.js frontend, a FastAPI backend, and Neo4j for graph storage, it helps users trace event dependencies, visualize causal relationships, simulate alternate timelines, and observe how changes propagate through a connected system.

## What It Is

- Graph-based timeline modeling system for causally linked events
- Interactive archive for events, characters, planets, and factions
- Alternate-timeline simulator for testing "what if" breaks in event chains
- State-replay system that reconstructs the world before a selected event by applying prior changes such as character deaths, planet control shifts, and artifact movement

## Key Features

- Chronology-aware event timeline with filters for era, character, location, order, and date range
- Slug-based detail pages for events, characters, planets, and factions
- Causal graph views for event dependencies, consequences, and alternate simulated branches
- Search across events, characters, planets, and factions
- Relationship authoring API for causal links and world-state changes authored by events
- Curated backfill pipeline for loading state-changing event history into Neo4j

## Visual Tour

### Landing Page

![Landing page](docs/images/event-causal-graph.webp)

### Event Causal Graph

![Event causal graph](docs/images/landing-page.webp)

### What-If Simulation

![What-if simulation](docs/images/what-if-simulation.webp)

### Universe State Snapshot

![Universe state snapshot](docs/images/universe-state.webp)

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

- `/` landing page with archive search and section navigation
- `/events` main timeline explorer and search results view
- `/events/[slug]` event detail page with causal graph, impact, what-if simulation, and universe state
- `/characters` character index
- `/characters/[slug]` character detail page
- `/planets` planet index
- `/planets/[slug]` planet detail page
- `/factions` faction index
- `/factions/[slug]` faction detail page with related characters, enemy factions, and involved events

Examples:

- `http://localhost:3000/`
- `http://localhost:3000/events`
- `http://localhost:3000/events/battle-of-yavin?depth=2`
- `http://localhost:3000/characters/luke-skywalker`

## Example Use Case

1. Open `/`.
2. Use the `Events` launcher or go directly to `/events`.
3. Select `Battle of Yavin`.
4. View its causal graph.
5. Toggle `What If?`.
6. Observe downstream events become invalidated or unresolved.

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

Production request and ingestion lifecycle:

![Production request and ingestion lifecycle](docs/production-request-ingestion-lifecycle.svg)

## Docs

- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Engineering Design](docs/engineering-design.md)

### Documentation

- Architecture diagrams: production request and ingestion lifecycle view in [docs/architecture.md](docs/architecture.md)
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

Focused simulation stress test:

```bash
cd backend
pytest tests/unit/engine/test_chaos_simulation.py
```

`tests/unit/engine/test_chaos_simulation.py` builds a deterministic 500-event mock tree, breaks events sampled across multiple topological ranks, and verifies that `TimelineSimulationService` produces stable downstream `BROKEN`, `INVALIDATED`, and `UNRESOLVED` states without unhandled execution errors.
