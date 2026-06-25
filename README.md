# Holocron Timeline Engine

I built this as a causal timeline system for a fictional universe, using Star Wars data as the working dataset. The core idea is simple: events are nodes, causal links are edges, and the backend can answer questions like "what had to happen before this?" or "what breaks if this event never happens?"

The stack is Next.js on the frontend, FastAPI in the backend, and Neo4j as the graph store. The frontend is mostly a thin client over the API. The backend owns chronology normalization, traversal rules, relationship validation, break simulation, and world-state reconstruction.

## What it does

- Lists events on a timeline with filters for era, character, location, and date range
- Traverses upstream dependencies and downstream consequences through `CAUSES` edges
- Renders event-focused causal graphs
- Runs a what-if simulation by breaking one event and propagating the effect through the downstream graph
- Reconstructs world state before a selected event by replaying prior state-changing relationships

## How it works

Events, characters, planets, and factions live in Neo4j. Events can also write state-changing edges such as "this event kills a character" or "this event changes who controls a planet." When you request a universe-state snapshot, the backend replays those earlier mutations in chronology order and returns the projected state for that point in time.

For simulation, the backend loads the downstream causal subgraph for a focus event, computes a topological order, marks the selected event as broken, and then walks the graph to decide which later events become invalidated or unresolved. The frontend keeps one React Flow canvas alive and swaps between canonical and simulated data instead of mounting separate graphs.

## Tradeoffs

I chose Neo4j over a relational model because the main read paths are graph traversals, not joins over tabular records. That made dependency expansion, consequence traversal, and path-oriented queries much simpler to express, but it also means the project depends on a more specialized database.

I kept the FastAPI layer effectively stateless with respect to the graph. I did not build a global in-memory graph cache because that complicates horizontal scaling and cache invalidation. The tradeoff is that deep traversals and graph assembly happen live against Neo4j, so some endpoints are more expensive than a precomputed design would be.

For universe-state projection, I added checkpoint caching to avoid replaying the full mutation history on every request. The safer version now uses database-derived cache versioning plus TTL and bounded cache size, but it is still an in-process optimization, not a full distributed cache.

## Limits and scaling constraints

This project is fine at small-to-medium graph sizes, but the expensive paths are clear:

- deep dependency and consequence traversals
- large causal graph payloads
- what-if simulations over large downstream branches
- universe-state projection when the mutation catalog grows

Public traversal depth is capped at `1..8` to avoid unbounded Cypher expansion. Neo4j reads also run with a query timeout. If this had to scale much further, the next steps would be tighter result limits, more query tuning, precomputed summaries for hot views, and probably a real distributed cache for universe-state reads.

## Example flow

The clearest example is the event detail page:

1. Open `/events`
2. Select `Battle of Yavin`
3. Load its causal graph
4. Toggle `What If?`
5. Watch downstream events shift to `broken`, `invalidated`, or `unresolved`

That flow is the reason the project exists. Most of the system is there to make that propagation behavior correct and explainable.

## Project structure

- `frontend/` contains the Next.js UI
- `backend/app/api/` contains FastAPI routes
- `backend/app/engine/` contains the actual application logic
- `backend/app/repositories/neo4j/` contains Cypher-backed persistence code
- `docs/architecture.md` explains system mechanics and scaling behavior
- `docs/api.md` documents the API surface

Request flow:

`Next.js UI -> FastAPI routes -> engine services -> Neo4j repositories -> Neo4j`

## Screens

![Landing page](docs/images/event-causal-graph.webp)
![Event causal graph](docs/images/landing-page.webp)
![What-if simulation](docs/images/what-if-simulation.webp)
![Universe state snapshot](docs/images/universe-state.webp)

## Run it locally

```bash
docker compose -f docker/compose.yml up --build
```

Local endpoints:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`
- Neo4j Browser: `http://localhost:7474`

## Data and tests

Transform and ingest data:

```bash
uv run python scripts/transform.py
uv run python scripts/ingest.py
```

Backfill curated state-changing event history:

```bash
cd backend
python -m app.scripts.backfill_temporal_mutations --dry-run
python -m app.scripts.backfill_temporal_mutations
```

Run tests:

```bash
cd backend
pytest
```

Focused simulation stress test:

```bash
cd backend
pytest tests/unit/engine/test_chaos_simulation.py
```

## Further reading

- [docs/architecture.md](docs/architecture.md)
- [docs/api.md](docs/api.md)
- [docs/engineering-design.md](docs/engineering-design.md)
