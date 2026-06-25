# Architecture

## Overview

Holocron Timeline Engine stores events and related entities in Neo4j, then uses that graph for traversal-heavy reads and mutation replay.

- `frontend/` is a Next.js UI for search, timeline browsing, graph views, and break simulation
- `backend/app/api/` exposes FastAPI routes under `/api/v1`
- `backend/app/engine/` contains traversal, simulation, relationship validation, and universe-state replay
- `backend/app/repositories/neo4j/` translates service calls into Cypher
- Neo4j is the source of truth

Request flow:

`Frontend -> FastAPI routes -> engine services -> Neo4j repositories -> Neo4j`

## Architecture Diagrams

![Production request and ingestion lifecycle](./production-request-ingestion-lifecycle.svg)

The codebase keeps two paths separate:

- stateless reads from the UI through FastAPI into request-scoped Neo4j queries
- ingestion and backfill jobs that validate writes before committing them to the same graph

### Runtime Layers

- `frontend/` issues browser-side REST calls and renders timeline, graph, and simulation views
- `backend/app/api/` and `backend/app/engine/` stay stateless with respect to graph topology and assemble subgraphs per request
- `backend/app/repositories/neo4j/` translates read and write operations into Cypher against Neo4j
- `scripts/`, `backend/app/ingestion/`, and backfill CLIs handle dataset compilation, audits, and idempotent writes outside the request path

## Core Model

### Node Types

- `Event`
- `Character`
- `Planet`
- `Faction`

### Relationship Types

- Structural: `CAUSES`, `INVOLVES`, `LOCATED_IN`, `MEMBER_OF`, `ALLIED_WITH`, `ENEMY_OF`
- State-changing: `SETS_ALIVE_STATE`, `SETS_CHARACTER_LOCATION`, `SETS_PLANET_CONTROL`, `SETS_ARTIFACT_LOCATION`

The structural edges describe chronology and archive relationships. The `SETS_*` edges carry state changes authored by events.

## System Mechanics

### Chronology Normalization

Chronology is stored as signed integers:

- `32 BBY` -> `-32`
- `4 ABY` -> `4`
- `0 ABY` -> `0`

This keeps filtering, sorting, traversal, and replay on one numeric axis.

### Zero-Boundary Behavior

Cross-boundary events are stored as normal intervals:

- `1 BBY -> 1 ABY` becomes `start_year = -1`, `end_year = 1`

Display chronology has no historical year zero, but the backend keeps a mathematical `0` internally so:

- interval math stays continuous
- comparisons and indexing do not need boundary-specific rules
- replay and offset calculations do not need BBY/ABY special cases

`0` exists to make the math work. It is not a lore claim.

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

`TimelineSimulationService` powers `GET /api/v1/engine/simulate-break/{event_id}`.

### Inputs

- selected event
- downstream causal subgraph
- dependency metadata for affected events

### Processing

The service:

1. marks the selected event as `broken`
2. computes a topological order over the downstream subgraph
3. evaluates each event from its dependency status
4. marks nodes as `invalidated` or `unresolved` based on which upstream dependencies still survive

### Output

The response returns:

- simulation nodes with status and dependency counts
- causal edges
- topological order

The frontend renders both the stored graph and the simulated graph in one React Flow canvas and reruns layout over whichever dataset is active.

## Scaling Characteristics

The backend does not keep a shared in-memory graph.

- Neo4j is the source of truth
- FastAPI instances are stateless with respect to graph topology
- traversals run through Cypher queries
- simulation logic runs on request-scoped subgraphs

### Why This Helps

- there is no cross-instance graph cache to invalidate
- adding app instances is straightforward
- writes are visible on the next read from Neo4j

### Main Bottlenecks

- deep Neo4j traversals
- large graph and simulation payloads
- Python post-processing over returned subgraphs
- frontend rendering once node and edge counts climb

### Likely Upgrade Paths

- tighter depth and payload limits
- more aggressive Cypher tuning and indexing
- precomputed summaries for hot graph views
- Neo4j Graph Data Science for heavier analysis
- Redis or pub/sub only if we later introduce shared in-memory graph materialization

## Mutation and Universe State

Events change world state through mutation edges. We do not store full snapshots on graph nodes.

### Mutation Rules

`RelationshipService` validates writes before persisting them:

- endpoints must exist
- unsupported source/target combinations are rejected
- self-referential edges are rejected
- duplicate edges are rejected
- `CAUSES` edges cannot introduce cycles
- `CAUSES` edges cannot violate chronology
- symmetric relationships are normalized to a stable endpoint order

### Universe-State Reconstruction

`UniverseStateService` reconstructs the world before a focus event from:

- curated baseline state
- prior events
- prior `SETS_*` mutations

It replays mutations in chronology order to derive:

- character alive/location state
- faction control by planet
- artifact holder or location

### Checkpoints

Universe-state reads use checkpoints at era boundaries so repeated requests replay only the remaining delta.

Tradeoff:

- warm reads are faster
- snapshots stay in-process because rebuilding them every time is wasteful
- cache reuse is gated by a database-derived version token, so instances rebuild after graph writes
- TTL and entry-count caps keep process memory bounded

This is a middle ground: faster than replaying from scratch, simpler than introducing Redis just for this path.

### Backfill

Curated state history is loaded through `TemporalMutationBackfillService`, which resolves slugs and writes through the same validation path as the API.

## Repository and Data Flow

- `Neo4jEventRepository` handles event listing, traversal, causal graph assembly, impact analysis, and break-simulation queries
- `Neo4jGraphRepository` stores relationships, validates references, runs search, and lists prior state mutations
- character, planet, and faction repositories handle lookup and creation

Data import stays outside the HTTP layer:

- `scripts/transform.py` compiles archive data
- `scripts/ingest.py` loads the transformed dataset
- `scripts/seed/init_schema.cypher` initializes Neo4j schema
- `scripts/audit/relationship_integrity.cypher` audits graph integrity

## Example Queries

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
