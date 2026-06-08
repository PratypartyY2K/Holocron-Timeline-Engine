# Holocron Timeline Engine

Holocron Timeline Engine is an interactive Star Wars knowledge graph and timeline explorer built with:

- Next.js 15
- FastAPI
- Neo4j
- a pure Python engine layer for graph and timeline logic

## Repository Layout

```text
frontend/  Next.js application
backend/   FastAPI application and engine layer
docs/      architecture and API documentation
docker/    local container orchestration
scripts/   development and seed scripts
```

## MVP API Surface

- create event
- get event by id
- get event by slug
- list events
- create relationship
- list dependencies for an event
- list consequences for an event

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

## Backend Test Entry Point

```bash
cd backend
pytest
```

