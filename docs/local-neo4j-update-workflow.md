# Local Neo4j Update Workflow

This guide explains how a developer or another local user can update the Neo4j database when running Holocron Timeline Engine on their own machine.

## Overview

There are two supported ways to update the database:

1. Use the ingestion pipeline for structured or bulk dataset updates.
2. Use the backend API for smaller incremental changes such as creating entities or relationships.

In most cases, users should avoid editing Neo4j directly in the Neo4j Browser unless they are debugging or doing one-off investigation. The application’s ingestion and API layers enforce the rules that keep the graph valid.

## Prerequisites

Make sure the local stack is running.

With Docker Compose:

```bash
docker compose -f docker/compose.yml up --build
```

Local endpoints:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Neo4j Browser: `http://localhost:7474`

## Option 1: Bulk or Structured Updates Through Ingestion

Use this path when:

- adding or refreshing a larger dataset
- importing many events, factions, planets, or characters
- updating source-backed archive data

### Step 1: Transform the source data

```bash
uv run python scripts/transform.py
```

This prepares the input data into the format expected by the ingestion flow.

### Step 2: Ingest the transformed data

```bash
uv run python scripts/ingest.py
```

This loads the transformed dataset into the backend-managed graph model.

### Why use ingestion

The ingestion path is preferred for larger changes because it:

- keeps imports repeatable
- centralizes validation
- uses the same backend service rules as the application
- reduces the chance of invalid graph relationships

## Option 2: Curated Temporal Mutation Backfills

Use this path when:

- adding curated world-state mutations
- updating character deaths, artifact locations, or planet control history
- loading historical state changes tied to events

### Dry run first

```bash
cd backend
python -m app.scripts.backfill_temporal_mutations --dry-run
```

### Apply the backfill

```bash
cd backend
python -m app.scripts.backfill_temporal_mutations
```

### Why this exists

This path is specifically for curated temporal mutation edges that affect projected universe state. It goes through backend validation and is safer than writing those edges manually.

## Option 3: Small Incremental Updates Through the API

Use this path when:

- creating a small number of entities
- adding one relationship at a time
- testing new graph connections locally

Open Swagger UI:

- `http://localhost:8000/docs`

Common write endpoints:

- `POST /api/v1/events`
- `POST /api/v1/characters`
- `POST /api/v1/planets`
- `POST /api/v1/factions`
- `POST /api/v1/graph/relationships`

### Typical API workflow

1. Create any missing nodes first.
2. Add relationships after the source and target nodes exist.
3. Use `POST /api/v1/graph/relationships` for causal links, faction links, and temporal mutations.
4. Verify the result through the frontend or read endpoints.

### Why use the API

The API layer enforces important validation such as:

- preventing duplicate relationships
- rejecting unsupported node-type combinations
- rejecting invalid `CAUSES` chronology
- rejecting `CAUSES` cycles
- canonicalizing symmetric faction relationships such as `ALLIED_WITH` and `ENEMY_OF`

## Direct Neo4j Edits

Direct edits in Neo4j Browser are possible, but they are not the recommended update path.

Use direct edits only when:

- debugging a local issue
- inspecting data manually
- doing temporary experiments you fully understand

Risks of direct writes:

- bypassing backend validation
- creating duplicate or invalid relationships
- breaking chronology assumptions
- introducing state mutations the application does not expect

If direct edits are made, they should be treated as exceptional and verified carefully.

## Recommended Local Workflow for a New Developer

If starting from an empty local database:

1. Start the stack with Docker Compose.
2. Run `uv run python scripts/transform.py`.
3. Run `uv run python scripts/ingest.py`.
4. Run the temporal mutation backfill in dry-run mode.
5. Apply the temporal mutation backfill.
6. Open `http://localhost:3000` and verify the archive UI.
7. Use Swagger UI at `http://localhost:8000/docs` for small incremental updates.

## Verification After an Update

After making changes, verify them through one or more of:

- the relevant frontend page at `http://localhost:3000`
- Swagger UI read endpoints
- Neo4j Browser for inspection only

Useful frontend verification routes:

- `/events`
- `/events/[slug]`
- `/characters/[slug]`
- `/planets/[slug]`
- `/factions/[slug]`

## Rule of Thumb

- large or source-backed changes: use ingestion
- curated state-history changes: use the backfill script
- small manual edits: use the API
- direct Neo4j writes: avoid unless debugging
