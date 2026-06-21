# Holocron Timeline Engine

## Engineering Design Document

## 1. Overview

Holocron Timeline Engine is an interactive Star Wars knowledge graph and timeline explorer. The system combines:

- a Next.js frontend for timeline and graph exploration
- a FastAPI backend for HTTP and application orchestration
- a pure Python engine layer for domain logic and graph query orchestration
- a Neo4j database as the system of record for graph relationships

The MVP focuses on event-centric exploration:

- create events
- create graph relationships
- browse a chronological timeline
- inspect event details
- visualize graph context
- find dependencies of an event
- find consequences of an event
- find a path between two events

The primary architectural constraint is strict separation of concerns:

- HTTP concerns stay in API route and schema layers
- business rules stay in the engine layer
- persistence access is isolated behind repository interfaces
- frontend consumes stable API contracts and does not embed backend logic

## 2. Goals and Non-Goals

### Goals

- production-quality repository structure
- clean architecture with explicit boundaries
- type-safe contracts across backend layers
- testable engine logic independent of HTTP and database drivers
- Neo4j model that supports both graph exploration and timeline queries
- containerized local development with minimal setup friction

### Non-Goals for MVP

- authentication and authorization
- collaborative editing
- real-time subscriptions
- full-text search beyond simple indexed lookup
- large-scale ingestion pipelines
- media asset management

## 3. High-Level Architecture

```text
Next.js Frontend
    |
    v
FastAPI API Layer
    |
    v
Application / Service Layer
    |
    v
Engine Interfaces and Use Cases
    |
    v
Repository Interfaces
    |
    v
Neo4j Repository Implementations
    |
    v
Neo4j Database
```

### Layer Responsibilities

#### Frontend

- renders timeline explorer, graph explorer, event details, and relationship workflows
- owns view state, client-side navigation, and presentation logic
- communicates with backend only through HTTP APIs

#### API Layer

- validates requests and responses
- maps HTTP semantics to engine use cases
- performs dependency injection
- converts engine/domain errors into HTTP error responses

#### Engine Layer

- defines core use cases and interfaces
- enforces graph and timeline business rules
- remains independent of FastAPI, Neo4j driver, and HTTP concerns

#### Repository Layer

- translates engine operations into Neo4j Cypher queries
- encapsulates persistence details and transaction boundaries

## 4. Proposed Repository Structure

```text
holocron/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── lib/
│   ├── hooks/
│   ├── styles/
│   ├── public/
│   ├── tests/
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.ts
├── backend/
│   ├── app/
│   ├── tests/
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env.example
├── docs/
│   ├── engineering-design.md
│   ├── api-contract.md
│   ├── schema.md
│   └── decisions/
├── docker/
│   ├── compose.yml
│   ├── neo4j/
│   │   ├── conf/
│   │   └── plugins/
│   └── backend/
├── scripts/
│   ├── dev/
│   ├── ci/
│   └── seed/
└── README.md
```

### Structure Rationale

- `frontend/` and `backend/` are independently buildable and deployable
- `docs/` stores durable architectural decisions and API/schema references
- `docker/` centralizes local orchestration concerns
- `scripts/` holds reproducible operational scripts instead of ad hoc shell usage

## 4A. Tradeoffs

The current design intentionally favors clarity and scale-out simplicity over squeezing every possible optimization into the MVP.

- Neo4j was chosen over a relational database because causal traversal, dependency expansion, and path-oriented graph queries are simpler to express and reason about in a native graph model. The tradeoff is accepting a more specialized persistence stack and a smaller hiring and tooling ecosystem than a conventional SQL deployment.
- The architecture avoids a global in-memory graph inside the FastAPI application. That reduces boot-time hydration work and removes cross-instance graph synchronization problems when the backend scales horizontally. The tradeoff is that traversal-heavy requests rely on live Neo4j reads instead of an already-materialized process-local graph.
- The backend is effectively stateless with respect to event and relationship topology. That makes container scaling, rolling deploys, and multi-instance consistency simpler. The tradeoff is higher query cost for deep graph assembly and repeated traversal work that a shared in-memory cache might avoid.

## 4B. Timeline Simulation Validation

The primary differentiator in the backend is the timeline break simulation flow, so it needs stronger validation than simple hand-authored examples.

- `TimelineSimulationService` is validated with focused deterministic unit tests for small hand-built graphs and a larger chaos harness.
- The chaos harness lives in `backend/tests/unit/engine/test_chaos_simulation.py`.
- That test programmatically builds a deterministic 500-event mock tree, injects mixed dependency shapes, and samples broken nodes from multiple topological ranks.
- For each simulated break, the test computes the expected downstream propagation independently and asserts exact node states, dependency counters, and topological order.
- The purpose is to catch execution-order bugs, unstable status propagation, and unhandled errors under larger downstream fan-out before any Neo4j integration is involved.

## 5. Backend Folder Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── dependencies/
│   │   ├── routes/
│   │   │   ├── events.py
│   │   │   ├── graph.py
│   │   │   ├── timeline.py
│   │   │   └── health.py
│   │   ├── errors.py
│   │   └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── lifespan.py
│   ├── domain/
│   │   ├── entities/
│   │   ├── value_objects/
│   │   ├── enums.py
│   │   └── errors.py
│   ├── engine/
│   │   ├── interfaces/
│   │   ├── services/
│   │   ├── policies/
│   │   └── dto/
│   ├── repositories/
│   │   ├── interfaces/
│   │   └── neo4j/
│   ├── schemas/
│   │   ├── common.py
│   │   ├── events.py
│   │   ├── graph.py
│   │   └── timeline.py
│   ├── db/
│   │   ├── neo4j.py
│   │   └── transaction.py
│   └── main.py
├── tests/
│   ├── unit/
│   │   └── engine/
│   ├── integration/
│   │   └── repositories/
│   └── fixtures/
├── pyproject.toml
├── Dockerfile
└── .env.example
```

### Backend Boundary Rules

- `api/` may depend on `schemas/`, `engine/`, `core/`, and `domain/errors`
- `engine/` may depend on `domain/` and repository interfaces only
- `repositories/neo4j/` may depend on `db/`, `domain/`, and engine/repository DTOs
- `domain/` depends on nothing outside itself
- `schemas/` are transport contracts and must not replace domain entities

## 6. Domain Model

The graph contains four primary node categories and six relationship categories.

### Node Types

#### Event

Represents a point or interval in the Star Wars timeline.

Core attributes:

- `id`: stable UUID and canonical backend identifier
- `slug`: URL-safe unique identifier used for frontend URLs
- `title`: canonical event title
- `description`: rich text or markdown-compatible plain text
- `start_year`: signed integer using a normalized galactic chronology convention
- `end_year`: optional signed integer for range events
- `era`: optional era label
- `canon_status`: enum for canon or legends if needed later
- `source_refs`: optional list of source identifiers
- `created_at`
- `updated_at`

#### Character

Core attributes:

- `id`: canonical backend identifier
- `slug`: frontend-friendly URL identifier
- `name`
- `description`
- `species`
- `homeworld_name` as a denormalized display field only if useful
- `created_at`
- `updated_at`

#### Planet

Core attributes:

- `id`: canonical backend identifier
- `slug`: frontend-friendly URL identifier
- `name`
- `description`
- `region`
- `created_at`
- `updated_at`

#### Faction

Core attributes:

- `id`: canonical backend identifier
- `slug`: frontend-friendly URL identifier
- `name`
- `description`
- `created_at`
- `updated_at`

### Relationship Types

#### CAUSES

- usually `Event -> Event`
- represents direct or strong causal influence

#### INVOLVES

- usually `Event -> Character | Faction`
- indicates participants or entities materially involved

#### LOCATED_IN

- usually `Event -> Planet`
- optionally `Character -> Planet` for homeworld or presence if later expanded

#### MEMBER_OF

- usually `Character -> Faction`

#### ALLIED_WITH

- usually `Faction <-> Faction`
- stored directionally in Neo4j but treated semantically as bidirectional

#### ENEMY_OF

- usually `Faction <-> Faction`
- stored directionally in Neo4j but treated semantically as bidirectional

## 7. Time Modeling Strategy

Time is central to the product, so it should be modeled explicitly instead of inferred from arbitrary labels.

### Proposed Time Fields for Event

- `start_year`: required integer
- `end_year`: optional integer
- `sort_year`: derived server-side as `start_year`
- `is_instant`: derived as `end_year is None or end_year == start_year`

### Chronology Convention

Use a single signed integer timeline at the storage and API boundary.

Example convention:

- negative values represent years before a reference epoch
- positive values represent years after that epoch

This avoids coupling the engine to string labels such as `19 BBY` or `4 ABY`. The frontend can format signed values into Star Wars presentation labels.

### Validation Rules

- `end_year` must be greater than or equal to `start_year`
- `title` and `slug` must be unique at the event level
- causal edges should not point backwards in time unless explicitly allowed by a future time-travel exception policy

## 8. Neo4j Schema Design

Neo4j uses labels, relationship types, property indexes, and constraints rather than a relational schema.

### Labels

- `Event`
- `Character`
- `Planet`
- `Faction`

### Node Property Constraints

Each label should have:

- uniqueness constraint on `id`
- uniqueness constraint on `slug`

Recommended:

- index on `Event.start_year`
- index on `Event.title`
- index on `Character.name`
- index on `Planet.name`
- index on `Faction.name`

### Relationship Property Strategy

Relationships should remain lightweight for MVP. Where needed, include:

- `id`: stable UUID for relationship mutation support
- `created_at`
- `updated_at`
- `note`: optional descriptive context

### Relationship Direction Rules

- `CAUSES`: `(:Event)-[:CAUSES]->(:Event)`
- `INVOLVES`: `(:Event)-[:INVOLVES]->(:Character|:Faction)`
- `LOCATED_IN`: `(:Event)-[:LOCATED_IN]->(:Planet)`
- `MEMBER_OF`: `(:Character)-[:MEMBER_OF]->(:Faction)`
- `ALLIED_WITH`: canonicalize lexicographically or by UUID to avoid duplicate reciprocal edges
- `ENEMY_OF`: canonicalize similarly

### Canonicalization Rule for Symmetric Edges

For `ALLIED_WITH` and `ENEMY_OF`, only one stored relationship should exist between a pair of factions. The repository layer should enforce a canonical source-target ordering to prevent duplicates.

### Query Implications

- timeline browsing uses indexed `Event.start_year`
- event dependencies use variable-length incoming `CAUSES` traversals
- event consequences use variable-length outgoing `CAUSES` traversals
- pathfinding uses shortest-path or bounded path queries between `Event` nodes
- graph visualization uses neighborhood expansion from a selected node with configurable depth and edge filtering

## 9. Pydantic Model Design

Pydantic models should be split by concern:

- request models
- response models
- internal DTOs if HTTP-facing shape differs from engine/domain shape

### Common Enums

#### NodeType

- `event`
- `character`
- `planet`
- `faction`

#### RelationshipType

- `causes`
- `involves`
- `located_in`
- `member_of`
- `allied_with`
- `enemy_of`

### Request Models

#### CreateEventRequest

Fields:

- `slug: str`
- `title: str`
- `description: str | None`
- `start_year: int`
- `end_year: int | None`
- `era: str | None`
- `canon_status: str | None`
- `source_refs: list[str]`

Validation:

- non-empty `slug`
- non-empty `title`
- `end_year >= start_year`

#### CreateRelationshipRequest

Fields:

- `type: RelationshipType`
- `from_node_id: str`
- `to_node_id: str`
- `note: str | None`

Validation:

- relationship type must be allowed for the participating node types
- self-referential edges allowed only when explicitly supported

#### TimelineQueryRequest

Fields:

- `start_year: int | None`
- `end_year: int | None`
- `limit: int = 50`
- `offset: int = 0`
- `order: Literal["asc", "desc"] = "asc"`

#### PathQueryRequest

Fields:

- `from_event_id: str`
- `to_event_id: str`
- `max_depth: int = 6`

#### GraphNeighborhoodRequest

Fields:

- `node_id: str`
- `depth: int = 1`
- `include_relationship_types: list[RelationshipType] | None`
- `limit_per_hop: int | None`

### Response Models

#### EventSummaryResponse

Fields:

- `id`
- `slug`
- `title`
- `start_year`
- `end_year`
- `era`

#### EventDetailResponse

Fields:

- event core attributes
- `dependencies: list[RelatedEventResponse]`
- `consequences: list[RelatedEventResponse]`
- `characters: list[CharacterSummaryResponse]`
- `factions: list[FactionSummaryResponse]`
- `planets: list[PlanetSummaryResponse]`

#### RelationshipResponse

Fields:

- `id`
- `type`
- `from_node_id`
- `to_node_id`
- `note`

#### GraphNodeResponse

Fields:

- `id`
- `type`
- `label`
- `subtitle: str | None`
- `metadata: dict[str, str | int | float | bool | None]`

#### GraphEdgeResponse

Fields:

- `id`
- `type`
- `source`
- `target`
- `label: str | None`

#### GraphResponse

Fields:

- `nodes: list[GraphNodeResponse]`
- `edges: list[GraphEdgeResponse]`

#### TimelinePageResponse

Fields:

- `items: list[EventSummaryResponse]`
- `total: int`
- `limit: int`
- `offset: int`

#### EventPathResponse

Fields:

- `events: list[EventSummaryResponse]`
- `edges: list[RelationshipResponse]`
- `depth: int`

## 10. Engine Interfaces

The engine layer should expose explicit interfaces rather than leaking repository details into routes.

### Core Engine Services

#### EventService

Responsibilities:

- create event
- fetch event by id or slug
- validate event chronology
- aggregate event detail views

Proposed methods:

- `create_event(command) -> Event`
- `get_event(event_id) -> Event`
- `get_event_by_slug(slug) -> Event`
- `get_event_detail(event_id) -> EventDetail`

#### RelationshipService

Responsibilities:

- create validated relationships
- enforce allowed node pairings
- canonicalize symmetric faction relationships

Proposed methods:

- `create_relationship(command) -> Relationship`

#### TimelineService

Responsibilities:

- browse events chronologically
- paginate and filter by time range

Proposed methods:

- `list_events(query) -> TimelinePage`

#### DependencyService

Responsibilities:

- find all upstream causes for an event
- find all downstream consequences for an event

Proposed methods:

- `get_dependencies(event_id, depth=None) -> list[Event]`
- `get_consequences(event_id, depth=None) -> list[Event]`

#### PathfindingService

Responsibilities:

- find graph path between two events
- validate source and target existence
- bound traversal depth for performance

Proposed methods:

- `find_event_path(from_event_id, to_event_id, max_depth) -> EventPath`

#### GraphExplorerService

Responsibilities:

- fetch local graph neighborhood for visualization
- map domain entities into graph-oriented node and edge DTOs

Proposed methods:

- `get_neighborhood(node_id, depth, filters) -> GraphView`

## 11. Repository Interfaces

Repository interfaces should reflect business use cases, not raw driver mechanics.

### EventRepository

Methods:

- `create(event: Event) -> Event`
- `get_by_id(event_id: str) -> Event | None`
- `get_by_slug(slug: str) -> Event | None`
- `list_by_time_range(start_year: int | None, end_year: int | None, limit: int, offset: int, order: str) -> tuple[list[Event], int]`
- `list_dependencies(event_id: str, depth: int | None) -> list[Event]`
- `list_consequences(event_id: str, depth: int | None) -> list[Event]`
- `find_event_path(from_event_id: str, to_event_id: str, max_depth: int) -> EventPathResult | None`

### GraphRepository

Methods:

- `create_relationship(relationship: Relationship) -> Relationship`
- `get_neighborhood(node_id: str, depth: int, filters: GraphFilter) -> GraphResult`
- `get_event_related_entities(event_id: str) -> EventRelationsBundle`
- `node_exists(node_id: str) -> bool`
- `get_node_type(node_id: str) -> NodeType | None`

### Transaction Boundary

For MVP, use per-request transaction scope managed by repository implementations or a lightweight unit-of-work abstraction. The engine should not manage driver sessions directly.

## 12. FastAPI Route Definitions

Route design should be resource-oriented and explicit.

### Health

#### `GET /api/v1/health`

Purpose:

- liveness/readiness signal

Response:

- service status
- optional Neo4j connectivity status

### Events

#### `POST /api/v1/events`

Purpose:

- create an event

Request body:

- `CreateEventRequest`

Response:

- `EventDetailResponse`

#### `GET /api/v1/events/{event_id}`

Purpose:

- fetch event details by canonical backend ID

Response:

- `EventDetailResponse`

#### `GET /api/v1/events/by-slug/{slug}`

Purpose:

- fetch event details by slug for frontend URL routing

Response:

- `EventDetailResponse`

### Timeline

#### `GET /api/v1/timeline/events`

Query params:

- `start_year`
- `end_year`
- `limit`
- `offset`
- `order`

Response:

- `TimelinePageResponse`

### Relationships

#### `POST /api/v1/graph/relationships`

Purpose:

- create any supported relationship

Request body:

- `CreateRelationshipRequest`

Response:

- `RelationshipResponse`

### Dependencies and Consequences

#### `GET /api/v1/events/{event_id}/dependencies`

Query params:

- `depth`

Response:

- `list[EventSummaryResponse]`

#### `GET /api/v1/events/{event_id}/consequences`

Query params:

- `depth`

Response:

- `list[EventSummaryResponse]`

### Pathfinding

#### `GET /api/v1/events/path`

Query params:

- `from_event_id`
- `to_event_id`
- `max_depth`

Response:

- `EventPathResponse`

### Graph Visualization

#### `GET /api/v1/graph/neighborhood`

Query params:

- `node_id`
- `depth`
- repeated `relationship_type`
- `limit_per_hop`

Response:

- `GraphResponse`

## 13. Dependency Injection Design

FastAPI dependency injection should wire infrastructure to interfaces at the API boundary.

### DI Principles

- routes depend on service interfaces or concrete service factories
- services depend on repository interfaces
- repository implementations depend on Neo4j driver/session providers
- configuration is injected from a typed settings object

### Recommended Dependency Providers

- `get_settings()`
- `get_neo4j_driver()`
- `get_event_repository()`
- `get_graph_repository()`
- `get_event_service()`
- `get_timeline_service()`
- `get_graph_explorer_service()`

### Why This Matters

- engine tests can use fake repositories with no HTTP or Neo4j dependency
- API tests can override service dependencies cleanly
- infrastructure can be swapped later with minimal route churn

## 14. Error Handling Strategy

Domain and application errors should be explicit and typed.

### Domain Errors

- `ValidationError`
- `EntityNotFoundError`
- `DuplicateEntityError`
- `UnsupportedRelationshipError`
- `ChronologyError`
- `PathNotFoundError`

### HTTP Mapping

- `EntityNotFoundError -> 404`
- `DuplicateEntityError -> 409`
- `ValidationError` and `ChronologyError -> 422`
- `UnsupportedRelationshipError -> 400`
- `PathNotFoundError -> 404`
- unexpected errors -> 500

## 15. Frontend Integration Contract

The frontend should be designed around stable API shapes rather than Neo4j-specific assumptions.

### Primary Screens

- timeline explorer
- event detail page
- graph explorer page or panel
- relationship creation flow

### Frontend Data Needs

#### Timeline Explorer

- paginated chronological events
- formatted year labels
- quick filters for time ranges

#### Event Detail

- event metadata
- upstream dependencies
- downstream consequences
- involved characters, factions, and locations

#### Graph Explorer

- graph nodes with type and label
- graph edges with type and display label
- neighborhood expansion controls

### API Contract Guidance

- prefer normalized IDs and stable enums
- avoid leaking raw Cypher or Neo4j shapes
- keep graph payloads generic enough for React Flow adapters

## 16. Testing Strategy

The engine layer is the highest-value unit testing target.

### Unit Tests

Focus:

- event validation rules
- allowed relationship pairing rules
- chronology constraints
- symmetric edge canonicalization
- dependency and consequence orchestration behavior
- pathfinding result mapping behavior with mocked repository outputs

### Integration Tests

Focus:

- Neo4j repository query correctness
- end-to-end route behavior against test dependencies

### Test Pyramid

- many engine unit tests
- fewer repository integration tests
- a modest number of API integration tests

## 17. Environment Configuration

Configuration should be fully environment-driven.

### Backend Environment Variables

- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `LOG_LEVEL`
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `NEO4J_DATABASE`
- `CORS_ALLOWED_ORIGINS`

### Frontend Environment Variables

- `NEXT_PUBLIC_API_BASE_URL`

### Configuration Rules

- typed settings via Pydantic Settings
- no hardcoded secrets
- `.env.example` checked into source control

## 18. Docker Compose Setup

The local stack should support frontend, backend, and Neo4j together.

### Services

#### `neo4j`

Responsibilities:

- primary graph database

Key configuration:

- expose Bolt and HTTP ports
- mount persistent data volume
- mount plugins/config directories only when needed
- initialize authentication via environment variables

#### `backend`

Responsibilities:

- FastAPI app

Key configuration:

- builds from `backend/Dockerfile`
- depends on Neo4j health or startup condition
- consumes environment variables from compose
- mounts backend source for local development if using reload

#### `frontend`

Responsibilities:

- Next.js app

Key configuration:

- builds from frontend project
- points to backend API base URL
- mounts source for local development if desired

### Compose File Placement

Use a single primary compose file:

- `docker/compose.yml`

### Volumes

- `neo4j_data`
- optional `neo4j_logs`

### Ports

- frontend: `3000`
- backend: `8000`
- Neo4j HTTP: `7474`
- Neo4j Bolt: `7687`

## 19. Suggested Initial Cypher Constraint Plan

This is design intent only, not implementation code.

Create:

- uniqueness on `Event.id`
- uniqueness on `Event.slug`
- uniqueness on `Character.id`
- uniqueness on `Character.slug`
- uniqueness on `Planet.id`
- uniqueness on `Planet.slug`
- uniqueness on `Faction.id`
- uniqueness on `Faction.slug`

Create indexes:

- `Event.start_year`
- `Event.title`
- `Character.name`
- `Planet.name`
- `Faction.name`

## 20. Initial Implementation Plan

### Phase 1: Foundation

- initialize repository structure
- set up backend packaging, linting, typing, and test tooling
- set up frontend with Next.js, TypeScript, Tailwind, and React Flow
- add Docker Compose for Neo4j, backend, and frontend
- add typed environment configuration

### Phase 2: Domain and Engine

- define domain entities, enums, and errors
- define repository interfaces
- implement engine DTOs and service interfaces
- implement engine business rules with unit tests first

### Phase 3: Persistence

- add Neo4j driver integration
- implement repository adapters with Cypher queries
- add repository integration tests
- add seed script for representative Star Wars sample data

### Phase 4: API

- add FastAPI app bootstrap and dependency providers
- implement event, timeline, graph, and pathfinding routes
- add OpenAPI-friendly Pydantic schemas
- add API tests for key flows

### Phase 5: Frontend MVP

- implement timeline page
- implement event detail page
- implement graph visualization with neighborhood fetch
- implement relationship creation UI

### Phase 6: Hardening

- improve logging and error responses
- validate performance of pathfinding and traversal queries
- add CI checks
- document local development, testing, and deployment workflows

## 21. Recommended Build Order

To reduce rework, implement in this order:

1. backend domain and engine contracts
2. engine unit tests
3. Neo4j repository adapters
4. FastAPI routes and dependency wiring
5. frontend API client and timeline view
6. graph visualization and path exploration
7. Docker and CI hardening

## 22. Key Risks and Mitigations

### Risk: Graph Query Complexity Grows Quickly

Mitigation:

- keep repository queries focused on MVP use cases
- avoid premature generic query builders

### Risk: Symmetric Relationship Duplication

Mitigation:

- enforce canonical ordering in engine or repository layer
- test duplication scenarios explicitly

### Risk: Timeline Semantics Become Inconsistent

Mitigation:

- normalize time to signed integers internally
- isolate display formatting to frontend utilities

### Risk: API Routes Accrete Business Logic

Mitigation:

- force route handlers to call engine services only
- review for HTTP-only concerns in API modules

### Risk: Pathfinding Performance on Large Graphs

Mitigation:

- enforce bounded depth
- add indexes and targeted traversal patterns
- revisit query strategy after sample data benchmarking

## 23. Approved MVP Decisions

The following decisions are approved for implementation:

- chronology is stored internally as a signed integer timeline
- `ALLIED_WITH` and `ENEMY_OF` are stored as canonical single edges
- MVP write APIs are limited to event creation and relationship creation
- MVP read APIs include get event, list events, dependency lookup, and consequence lookup

### Remaining Optional Decision

Resolved:

- backend canonical key is `id`
- frontend URL key is `slug`

## 24. Summary

This design uses a clean layered architecture with:

- Next.js for visualization and interaction
- FastAPI for transport and dependency injection
- a pure Python engine for business logic
- Neo4j for graph persistence

The design is intentionally event-centric for MVP and keeps the engine isolated from HTTP and database specifics. The approved MVP API surface is:

- event APIs: create event, get event, list events
- relationship APIs: create relationship, dependency lookup, consequence lookup

The next step, after final approval to proceed, is to scaffold the repository and implement the backend contracts and tests in the recommended build order.
