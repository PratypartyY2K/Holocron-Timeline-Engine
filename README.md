# Holocron Timeline Engine

Holocron Timeline Engine is an interactive Star Wars knowledge graph and timeline explorer built with:

- Next.js 15
- FastAPI
- Neo4j
- a pure Python engine layer for graph and timeline logic

## Current Product Surface

Frontend:

- `/events` timeline explorer
- timeline filters for chronology, order, and era
- slug-based event detail pages at `/events/{slug}`
- dependency and consequence panels with depth controls
- React Flow causal graph with node click navigation

Backend:

- event creation and retrieval
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
- `POST /api/v1/graph/relationships`
- `GET /api/v1/events/{event_id}/dependencies?depth=N`
- `GET /api/v1/events/{event_id}/consequences?depth=N`
- `GET /api/v1/events/{event_id}/causal-graph?depth=N`

## Local Development

Use Docker Compose for the full stack:

```bash
docker compose -f docker/compose.yml up --build
```

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

### Useful Frontend Routes

- timeline: `http://localhost:3000/events`
- detail page example: `http://localhost:3000/events/battle-of-yavin`
- filtered timeline example: `http://localhost:3000/events?era=Age%20of%20Rebellion&order=asc`
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
