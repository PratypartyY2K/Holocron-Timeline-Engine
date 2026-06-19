# Architecture

## Overview

Holocron Timeline Engine is split into a Next.js frontend, a FastAPI backend, and Neo4j as the persistent graph store. The backend follows a layered design:

- API routes handle HTTP request and response concerns
- Engine services apply business rules and orchestration
- Repository implementations run Neo4j queries
- Domain entities define the core data model

High-level flow:

`Frontend -> /api/v1 routes -> engine services -> Neo4j repositories -> Neo4j`

## Architecture Diagrams

### HLD

```text
+-------------------+       +-------------------+       +-------------------+
| Next.js Frontend  | ----> | FastAPI API Layer | ----> | Engine Services   |
+-------------------+       +-------------------+       +-------------------+
                                                              |
                                                              v
                                                     +-------------------+
                                                     | Neo4j Repositories|
                                                     +-------------------+
                                                              |
                                                              v
                                                     +-------------------+
                                                     | Neo4j Graph Store |
                                                     +-------------------+
```

### LLD

```text
frontend/app + components
        |
        v
backend/app/api/routes
        |
        v
backend/app/api/dependencies
        |
        v
backend/app/engine/services
        |
        v
backend/app/repositories/interfaces
        |
        v
backend/app/repositories/neo4j
        |
        v
backend/app/domain + backend/app/schemas
```

## System Structure

### Frontend

The frontend lives in `frontend/` and uses the App Router. It provides:

- the homepage search experience
- timeline browsing under `/events`
- slug-based entity detail pages
- event detail views with causal graph rendering and what-if simulation controls

The UI reads backend data through `frontend/lib/holocron-api.ts` and related client helpers, then renders the result in page-level client components such as `home-page-client.tsx`, `entity-pages-client.tsx`, and `event-detail-page-client.tsx`.

### Backend

The backend lives in `backend/app/` and is organized by responsibility:

- `api/` defines FastAPI routers, dependency injection, and error mapping
- `engine/services/` contains application logic
- `repositories/interfaces/` defines persistence contracts
- `repositories/neo4j/` implements those contracts with Cypher
- `domain/entities/` and `domain/enums.py` define the core model
- `schemas/` contains transport-layer request and response models

`backend/app/main.py` creates the FastAPI app, adds CORS and request logging middleware, then mounts all routes under `/api/v1`.

## Core Domain Model

The graph currently revolves around four node types:

- `Event`
- `Character`
- `Planet`
- `Faction`

The main relationship categories are:

- `CAUSES`
- `INVOLVES`
- `LOCATED_IN`
- `MEMBER_OF`
- `ALLIED_WITH`
- `ENEMY_OF`
- `SETS_ALIVE_STATE`
- `SETS_CHARACTER_LOCATION`
- `SETS_PLANET_CONTROL`
- `SETS_ARTIFACT_LOCATION`

The first six relationships describe graph structure and archive semantics. The `SETS_*` relationships are temporal mutations used to project timeline state over time.

## Data Model Diagram

```text
(Event)-[:CAUSES]->(Event)
(Event)-[:INVOLVES]->(Character)
(Event)-[:INVOLVES]->(Faction)
(Event)-[:LOCATED_IN]->(Planet)
(Character)-[:LOCATED_IN]->(Planet)
(Character)-[:MEMBER_OF]->(Faction)
(Faction)-[:ALLIED_WITH]->(Faction)
(Faction)-[:ENEMY_OF]->(Faction)

(Event)-[:SETS_ALIVE_STATE]->(Character)
(Event)-[:SETS_CHARACTER_LOCATION {subject_node_id=Character}]->(Planet)
(Event)-[:SETS_PLANET_CONTROL {subject_node_id=Planet}]->(Faction)
(Event)-[:SETS_ARTIFACT_LOCATION {artifact_key=...}]->(Character|Planet)
```

## Simulation Engine

The simulation engine is centered on `TimelineSimulationService`.

### Inputs

`GET /api/v1/engine/simulate-break/{event_id}` loads:

- the selected event
- a downstream causal subgraph
- dependency metadata for each downstream event

The graph data comes from the event repository, which returns:

- downstream events reachable through `CAUSES`
- internal causal edges among those events
- dependency ids keyed by event id

### Processing

The engine performs a topological traversal over the downstream subgraph:

1. It marks the selected event as `broken`.
2. It computes a topological order from the causal edges.
3. For each downstream event, it inspects the status of its dependencies.
4. It classifies the event as `invalidated` when all required support is broken.
5. It classifies the event as `unresolved` when some support survives or is itself unresolved.

Each simulation node also includes:

- `topological_rank`
- `affected_by_event_ids`
- `surviving_dependency_count`
- `broken_dependency_count`
- `unresolved_dependency_count`

### Output

The API returns a `TimelineBreakSimulationResponse` containing:

- the broken root event id
- enriched simulation nodes
- causal edges
- the computed topological order

The frontend uses that payload to swap the canonical event graph into an alternate branch view.

## Mutation System

The mutation system lets events author changes to world state without embedding those state snapshots directly on nodes.

### Mutation Relationship Types

The supported temporal mutation edges are:

- `SETS_ALIVE_STATE`
- `SETS_CHARACTER_LOCATION`
- `SETS_PLANET_CONTROL`
- `SETS_ARTIFACT_LOCATION`

These are created through the normal relationship API and validated by `RelationshipService`.

### Validation Rules

`RelationshipService` enforces several rules before writing a relationship:

- source and target nodes must exist
- the relationship type must be valid for the source/target node pair
- self-referential edges are rejected
- `CAUSES` edges cannot introduce cycles
- `CAUSES` edges cannot violate chronology ordering
- canonical symmetric relationships such as `ALLIED_WITH` and `ENEMY_OF` are normalized to a stable endpoint order
- duplicates are rejected based on type, endpoints, and mutation qualifiers such as `subject_node_id` or `artifact_key`

This keeps graph semantics and state changes consistent regardless of whether data enters through the API or backfill scripts.

### Universe State Reconstruction

`UniverseStateService` reconstructs a projected state before a focus event by combining:

- curated baseline state from `engine/universe_state_catalog.py`
- the full event list up to the focus event
- all mutation relationships that occur before the focus event

It starts from baseline values for tracked characters, faction control, and artifacts, then replays mutations in chronological order. The resulting `UniverseState` includes:

- character alive/location state
- faction control by planet
- artifact holder or location
- projection notes and metadata

This gives the event detail page a snapshot of the galaxy as of the selected point in the timeline.

### Backfill Workflow

`TemporalMutationBackfillService` turns curated aliases from `universe_state_catalog.py` into actual graph relationships. It:

- resolves event and entity slugs
- plans mutation writes
- skips missing entities and records diagnostics
- writes through `RelationshipService`
- treats duplicates as safe no-op skips

Because the backfill runs through the same validation path as the API, it keeps the mutation catalog and live graph rules aligned.

## Repository Responsibilities

The Neo4j repositories do more than raw CRUD:

- `Neo4jEventRepository` supports event listing, dependency traversal, consequence traversal, causal graph assembly, impact analysis, and break-simulation graph queries
- `Neo4jGraphRepository` validates node references, stores relationships, runs search, and lists prior state mutations
- character, planet, and faction repositories provide entity lookup and creation

The repositories also enrich event reads with computed fields such as dependency counts, faction slugs, and a simple centrality score.

## Ingestion and Seed Data

Archive content is prepared outside the HTTP layer:

- `scripts/transform.py` compiles raw data fragments into `data/processed/dataset.json`
- `scripts/ingest.py` pushes the transformed dataset through backend ingestion code
- `scripts/seed/init_schema.cypher` initializes Neo4j schema
- `scripts/audit/relationship_integrity.cypher` audits data integrity in the graph

This keeps import logic reproducible and lets the project reuse service-layer validation during ingest.

## Example Queries

Example Cypher patterns used by the system:

```cypher
MATCH (source:Event)-[:CAUSES*1..]->(target:Event {id: $event_id})
RETURN DISTINCT source
ORDER BY source.start_year ASC, source.title ASC
```

```cypher
MATCH (source:Event {id: $event_id})-[:CAUSES*1..]->(target:Event)
RETURN DISTINCT target
ORDER BY target.start_year ASC, target.title ASC
```

```cypher
MATCH (focus:Event {id: $event_id})
MATCH (source:Event)-[r]->()
WHERE type(r) IN [
  "SETS_ALIVE_STATE",
  "SETS_CHARACTER_LOCATION",
  "SETS_PLANET_CONTROL",
  "SETS_ARTIFACT_LOCATION"
]
RETURN properties(r) AS relationship
```
