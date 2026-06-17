# Holocron Timeline Engine

Holocron Timeline Engine is an interactive Star Wars knowledge graph and timeline explorer built with:

- Next.js 15
- FastAPI
- Neo4j
- a pure Python engine layer for graph and timeline logic

## Current Product Surface

Frontend:

- `/events` timeline explorer
- `/characters`, `/planets`, and `/factions` entity browsers
- archive-wide search across events, characters, planets, and factions
- character detail timelines driven by the character-specific timeline endpoint
- timeline filters for chronology, order, era, character, and location
- BBY/ABY chronology inputs that normalize Star Wars dates into signed years for filtering
- slug-based event detail pages at `/events/{slug}`
- slug-based entity detail pages at `/characters/{slug}`, `/planets/{slug}`, and `/factions/{slug}`
- dependency and consequence panels with depth controls
- React Flow causal graph with path tracing, node coloring controls, and node navigation
- automatic causal graph layout using `@dagrejs/dagre`
- chronology-aware left-to-right graph positioning for complex event paths
- interactive "What If?" sandbox toggle on event detail pages
- Butterfly Effect simulation that swaps the causal graph into an alternate branch view
- invalidated and unresolved downstream timeline states rendered directly in React Flow
- event graph coloring by graph tone, era, and involved faction
- main archive timeline zoomed and grouped by year or decade
- universe-state snapshot cards with linked character, faction, and planet detail pages
- browser-side data fetching for timeline, entity, and event detail API calls

Backend:

- event creation and retrieval
- character, planet, and faction creation and retrieval
- relationship creation
- temporal mutation creation through the relationship API
- dependency and consequence traversal
- causal graph endpoint for event-focused graph rendering
- impact analysis endpoint for downstream breakage simulation
- timeline break simulation endpoint for alternate branch propagation

## Repository Layout

```text
frontend/  Next.js application
backend/   FastAPI application and engine layer
docs/      architecture and API documentation
docker/    local container orchestration
scripts/   development and seed scripts
```

## MVP API Surface

- `POST /api/v1/events`
- `GET /api/v1/events`
- `GET /api/v1/events/{event_id}`
- `GET /api/v1/events/by-slug/{slug}`
- `GET /api/v1/search?q=anakin`
- `GET /api/v1/characters`
- `GET /api/v1/characters/by-slug/{slug}`
- `GET /api/v1/characters/{character_id}/timeline`
- `GET /api/v1/planets`
- `GET /api/v1/planets/by-slug/{slug}`
- `GET /api/v1/factions`
- `GET /api/v1/factions/by-slug/{slug}`
- `POST /api/v1/graph/relationships`
- `GET /api/v1/events/{event_id}/dependencies?depth=N`
- `GET /api/v1/events/{event_id}/consequences?depth=N`
- `GET /api/v1/events/{event_id}/causal-graph?depth=N`
- `GET /api/v1/events/{event_id}/impact`
- `GET /api/v1/engine/simulate-break/{event_id}`
- `GET /api/v1/events/{event_id}/universe-state`

`GET /api/v1/events` now supports combined filters such as:

- `era`
- `character`
- `location`
- `start_year`
- `end_year`
- `order`
- `limit`
- `offset`
- `causal_depth`

## Local Development

Use Docker Compose for the full stack:

```bash
docker compose -f docker/compose.yml up --build
```

The backend container runs `uvicorn --reload` in local Compose, so route and service changes
should be picked up automatically after file edits.

The frontend container now installs dependencies from `package-lock.json` with `npm ci`, so
dependency-sensitive UI changes such as graph layout packages are reproducible in Docker as
well as local Node installs.

Key endpoints:

- frontend: `http://localhost:3000`
- backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Neo4j browser: `http://localhost:7474`

### Browser API Behavior

The frontend now issues its data requests from the browser for the main archive, entity
listing pages, entity detail pages, and event detail pages. In browser DevTools, these
requests should appear as `fetch`/XHR calls to `http://localhost:8000/api/v1/...` rather
than only as top-level document navigations.

When `NEXT_PUBLIC_API_BASE_URL` is unset in the browser, the frontend defaults to
`http://localhost:8000`. In Docker Compose, server-side rendering can still use the
internal service hostname `http://backend:8000`, but browser-visible API traffic is
normalized to `localhost` so the requests resolve correctly from the user agent.

### Seed Neo4j Schema

Open Neo4j Browser and run the Cypher from:

```text
scripts/seed/init_schema.cypher
```

### Contributor Data Pipeline

Contributors do not need to write Cypher to add archive data.

Add JSON fragments under `data/raw/`, then transform and ingest them through the
backend pipeline:

```bash
uv run python scripts/transform.py
uv run python scripts/ingest.py
```

The transform step compiles raw fragments into `data/processed/dataset.json`.
The ingest step resolves slug-based references and writes through the backend's
service layer, so relationship validation and chronology rules are reused during
import.

### Audit Relationship Integrity

To audit existing graph data for relationship integrity violations, run:

```text
scripts/audit/relationship_integrity.cypher
```

The audit checks for:

- self-referential relationships
- duplicate relationships with the same type and endpoint pair
- relationship types attached to invalid source/target node label combinations
- non-canonical ordering for symmetric faction relationships

### Useful Frontend Routes

- timeline: `http://localhost:3000/events`
- archive search example: `http://localhost:3000/?q=anakin`
- character timeline example: `http://localhost:3000/characters/luke-skywalker`
- detail page example: `http://localhost:3000/events/battle-of-yavin`
- filtered timeline example: `http://localhost:3000/events?era=Age%20of%20Rebellion&order=asc`
- chronology filter example: `http://localhost:3000/?start_year=32%20BBY&end_year=4%20ABY`
- character-filtered timeline example: `http://localhost:3000/?character=wilhuff-tarkin`
- location-filtered timeline example: `http://localhost:3000/?location=tatooine`
- entity browser examples: `http://localhost:3000/characters`, `http://localhost:3000/planets`, `http://localhost:3000/factions`
- depth example: `http://localhost:3000/events/battle-of-yavin?depth=2`

### Timeline UX

The main archive timeline now supports frontend-only zoom/grouping modes:

- `Year view` groups events by exact chronology buckets
- `Decade view` groups events into decade bands while preserving the filtered event list

This works on top of the existing `GET /api/v1/events` payload and does not require a full-page
reload to move between zoom levels.

### What-If Sandbox

On an event detail page, the Sandbox toggle activates a Butterfly Effect simulation for the
currently focused event. The frontend fetches `GET /api/v1/engine/simulate-break/{event_id}`
on demand and replaces the canonical React Flow data with the alternate branch response.

The simulator:

- topologically sorts the downstream `CAUSES` graph from the broken event
- marks the selected event as `broken`
- marks downstream events as `invalidated` when their required support chain collapses
- marks downstream events as `unresolved` when some non-broken support still exists
- namespaces simulated node and edge ids in the UI so the alternate graph does not overlap the canonical one during the toggle

The older `GET /api/v1/events/{event_id}/impact` endpoint is still useful for impact summaries,
but the What-if graph now renders from the simulation endpoint directly.

The event detail experience also now includes:

- local dependency depth updates without reloading the full event page
- linked universe-state snapshot entities for tracked characters, planets, and factions
- graph path tracing between two selected nodes
- double-click node navigation into the selected event
- node coloring controls for graph tone, era, and faction involvement

### Temporal Mutations

You do not need to open Neo4j Browser to author timeline state changes. Temporal mutations can be
created through `POST /api/v1/graph/relationships` using the new event-authored mutation
relationship types:

- `SETS_ALIVE_STATE`
- `SETS_CHARACTER_LOCATION`
- `SETS_PLANET_CONTROL`
- `SETS_ARTIFACT_LOCATION`

Example payload for transferring planetary control:

```json
{
  "type": "SETS_PLANET_CONTROL",
  "from_node_id": "event-rise-empire",
  "to_node_id": "faction-empire",
  "subject_node_id": "planet-coruscant",
  "note": "Imperial takeover of Coruscant"
}
```

Example payload for recording a character death:

```json
{
  "type": "SETS_ALIVE_STATE",
  "from_node_id": "event-battle-yavin",
  "to_node_id": "char-grand-moff-tarkin",
  "value_bool": false,
  "note": "Destroyed aboard the first Death Star"
}
```

To backfill the current curated mutation catalog into Neo4j through the backend codepath, run:

```bash
cd backend
python -m app.scripts.backfill_temporal_mutations --dry-run
python -m app.scripts.backfill_temporal_mutations
```

The command uses the same repository and validation logic as the API. It is idempotent for the
currently curated mutations and will skip duplicates that already exist in Neo4j.

### Graph Layout

The event detail causal graph uses `@dagrejs/dagre` to compute a cleaner React Flow layout for
multi-node timelines. The layout engine handles vertical spacing and overlap avoidance, while
event chronology still determines the left-to-right column order so causal paths stay readable
as the graph grows. In What-if mode, the frontend remounts React Flow with a simulated graph id
namespace so alternate-branch nodes are treated as a distinct layout rather than reusing canonical
render state. The graph layer also supports click-to-anchor path highlighting and visual coloring
by era or faction to make dense event networks easier to inspect.

### Chronology Filters

Timeline filters accept Star Wars-native chronology strings such as `32 BBY`, `19 BBY`, and
`4 ABY` instead of forcing users to think in signed integers. The frontend parses those values
into normalized signed years before making API requests, so `32 BBY` becomes `-32`, `19 BBY`
becomes `-19`, and `4 ABY` becomes `4` for consistent backend filtering and sort behavior.

## Local Installation

### Backend

Using `uv`:

```bash
cd backend
uv venv
source .venv/bin/activate
uv sync --extra dev
cp .env.example .env
```

Using `pip`:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
```

### Frontend

```bash
cd frontend
npm install
```

## Testing

```bash
cd backend
pytest
```

Focused backend verification used during simulator work:

```bash
cd backend
pytest tests/unit/engine/test_timeline_simulation_service.py tests/unit/engine/test_event_service.py
```

Useful variants:

```bash
pytest tests/unit/engine
pytest -q
pytest --cov=app --cov-report=term-missing
```
