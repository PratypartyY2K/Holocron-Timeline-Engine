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
- slug-based event detail pages at `/events/{slug}`
- slug-based entity detail pages at `/characters/{slug}`, `/planets/{slug}`, and `/factions/{slug}`
- dependency and consequence panels with depth controls
- React Flow causal graph with node click navigation
- interactive "What If?" sandbox toggle on event detail pages
- broken-path simulation that deactivates the focus event and highlights impacted downstream nodes
- browser-side data fetching for timeline, entity, and event detail API calls

Backend:

- event creation and retrieval
- character, planet, and faction creation and retrieval
- relationship creation
- dependency and consequence traversal
- causal graph endpoint for event-focused graph rendering
- impact analysis endpoint for downstream breakage simulation

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
- character-filtered timeline example: `http://localhost:3000/?character=wilhuff-tarkin`
- location-filtered timeline example: `http://localhost:3000/?location=tatooine`
- entity browser examples: `http://localhost:3000/characters`, `http://localhost:3000/planets`, `http://localhost:3000/factions`
- depth example: `http://localhost:3000/events/battle-of-yavin?depth=2`

### What-If Sandbox

On an event detail page, the Sandbox toggle activates a what-if simulation for the
currently focused event. The frontend fetches `GET /api/v1/events/{event_id}/impact`
on demand, then uses the returned downstream events and broken `CAUSES` edges to:

- gray out the selected event as deactivated
- mark downstream impacted events as broken
- highlight the broken causal path directly in the React Flow graph

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

Useful variants:

```bash
pytest tests/unit/engine
pytest -q
pytest --cov=app --cov-report=term-missing
```
