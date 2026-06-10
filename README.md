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
- timeline filters for chronology, order, era, character, and location
- slug-based event detail pages at `/events/{slug}`
- slug-based entity detail pages at `/characters/{slug}`, `/planets/{slug}`, and `/factions/{slug}`
- dependency and consequence panels with depth controls
- React Flow causal graph with node click navigation

Backend:

- event creation and retrieval
- character, planet, and faction creation and retrieval
- relationship creation
- dependency and consequence traversal
- causal graph endpoint for event-focused graph rendering

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
- `GET /api/v1/characters`
- `GET /api/v1/characters/by-slug/{slug}`
- `GET /api/v1/planets`
- `GET /api/v1/planets/by-slug/{slug}`
- `GET /api/v1/factions`
- `GET /api/v1/factions/by-slug/{slug}`
- `POST /api/v1/graph/relationships`
- `GET /api/v1/events/{event_id}/dependencies?depth=N`
- `GET /api/v1/events/{event_id}/consequences?depth=N`
- `GET /api/v1/events/{event_id}/causal-graph?depth=N`

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
- detail page example: `http://localhost:3000/events/battle-of-yavin`
- filtered timeline example: `http://localhost:3000/events?era=Age%20of%20Rebellion&order=asc`
- character-filtered timeline example: `http://localhost:3000/?character=wilhuff-tarkin`
- location-filtered timeline example: `http://localhost:3000/?location=tatooine`
- entity browser examples: `http://localhost:3000/characters`, `http://localhost:3000/planets`, `http://localhost:3000/factions`
- depth example: `http://localhost:3000/events/battle-of-yavin?depth=2`

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
