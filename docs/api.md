# API

Base URL: `http://localhost:8000/api/v1`

Interactive docs:

- Swagger UI: `http://localhost:8000/docs`

## Endpoint Groups

### Health

- `GET /health`

### Search

- `GET /search`

### Events

- `POST /events`
- `GET /events`
- `GET /events/{event_id}`
- `GET /events/by-slug/{slug}`
- `GET /events/{event_id}/universe-state`

### Graph

- `POST /graph/relationships`
- `GET /events/{event_id}/dependencies`
- `GET /events/{event_id}/consequences`
- `GET /events/{event_id}/causal-graph`
- `GET /events/{event_id}/impact`

### Simulation

- `GET /engine/simulate-break/{event_id}`
- `GET /characters/{character_id}/timeline`

### Characters

- `POST /characters`
- `GET /characters`
- `GET /characters/by-slug/{slug}`

### Planets

- `POST /planets`
- `GET /planets`
- `GET /planets/by-slug/{slug}`

### Factions

- `POST /factions`
- `GET /factions`
- `GET /factions/by-slug/{slug}`

## Health

### `GET /health`

Returns a simple status payload.

## Search

### `GET /search`

Searches across events, characters, planets, and factions.

Query parameters:

- `q` required search string, minimum length 1
- `limit` optional, default `10`, range `1..25`

## Example Requests

### Example 1: List timeline events with filters

Request:

```http
GET /api/v1/events?era=Reign%20of%20the%20Empire&start_year=0&end_year=10&order=asc&limit=2 HTTP/1.1
Host: localhost:8000
Accept: application/json
```

Response:

```json
{
  "items": [
    {
      "id": "evt_yavin",
      "slug": "battle-of-yavin",
      "title": "Battle of Yavin",
      "description": "The Rebel Alliance destroys the first Death Star.",
      "start_year": 0,
      "end_year": 0,
      "era": "Reign of the Empire",
      "canon_status": "canon",
      "dependency_count": 3,
      "centrality_score": 0.84,
      "source_refs": ["A New Hope"],
      "faction_slugs": ["rebel-alliance", "galactic-empire"],
      "faction_names": ["Rebel Alliance", "Galactic Empire"],
      "created_at": "2026-06-20T12:00:00Z",
      "updated_at": "2026-06-20T12:00:00Z"
    }
  ],
  "total": 1,
  "limit": 2,
  "offset": 0
}
```

### Example 2: Simulate a causal break

Request:

```http
GET /api/v1/engine/simulate-break/evt_yavin HTTP/1.1
Host: localhost:8000
Accept: application/json
```

Response:

```json
{
  "broken_event_id": "evt_yavin",
  "nodes": [
    {
      "id": "evt_yavin",
      "slug": "battle-of-yavin",
      "title": "Battle of Yavin",
      "description": "The Rebel Alliance destroys the first Death Star.",
      "start_year": 0,
      "end_year": 0,
      "era": "Reign of the Empire",
      "canon_status": "canon",
      "dependency_count": 3,
      "centrality_score": 0.84,
      "source_refs": ["A New Hope"],
      "faction_slugs": ["rebel-alliance", "galactic-empire"],
      "faction_names": ["Rebel Alliance", "Galactic Empire"],
      "created_at": "2026-06-20T12:00:00Z",
      "updated_at": "2026-06-20T12:00:00Z",
      "status": "broken",
      "topological_rank": 12,
      "affected_by_event_ids": [],
      "surviving_dependency_count": 0,
      "broken_dependency_count": 0,
      "unresolved_dependency_count": 0
    },
    {
      "id": "evt_endor",
      "slug": "battle-of-endor",
      "title": "Battle of Endor",
      "description": "The second Death Star is destroyed.",
      "start_year": 4,
      "end_year": 4,
      "era": "Reign of the Empire",
      "canon_status": "canon",
      "dependency_count": 2,
      "centrality_score": 0.73,
      "source_refs": ["Return of the Jedi"],
      "faction_slugs": ["rebel-alliance", "galactic-empire"],
      "faction_names": ["Rebel Alliance", "Galactic Empire"],
      "created_at": "2026-06-20T12:00:00Z",
      "updated_at": "2026-06-20T12:00:00Z",
      "status": "invalidated",
      "topological_rank": 18,
      "affected_by_event_ids": ["evt_yavin"],
      "surviving_dependency_count": 1,
      "broken_dependency_count": 1,
      "unresolved_dependency_count": 0
    }
  ],
  "edges": [
    {
      "id": "rel_yavin_endor",
      "source_id": "evt_yavin",
      "target_id": "evt_endor",
      "type": "CAUSES",
      "note": "Destroys the first Death Star and preserves the rebellion."
    }
  ],
  "topological_order": ["evt_yavin", "evt_endor"]
}
```

### Example 3: Read projected universe state before an event

Request:

```http
GET /api/v1/events/evt_endor/universe-state HTTP/1.1
Host: localhost:8000
Accept: application/json
```

Response:

```json
{
  "event_id": "evt_endor",
  "event_slug": "battle-of-endor",
  "event_title": "Battle of Endor",
  "as_of_year": 4,
  "prior_event_count": 27,
  "projection_mode": "checkpoint-plus-delta",
  "notes": [
    "Projection resumes from the nearest cached checkpoint before replaying later mutations."
  ],
  "characters": [
    {
      "id": "char_luke",
      "slug": "luke-skywalker",
      "name": "Luke Skywalker",
      "is_alive": true,
      "location_planet_slug": "endor",
      "location_planet_name": "Endor"
    }
  ],
  "faction_control": [
    {
      "planet_slug": "coruscant",
      "planet_name": "Coruscant",
      "faction_slug": "galactic-empire",
      "faction_name": "Galactic Empire"
    }
  ],
  "artifacts": [
    {
      "artifact_key": "death-star-ii-plans",
      "artifact_name": "Death Star II Plans",
      "holder_character_slug": null,
      "holder_character_name": null,
      "location_planet_slug": "endor",
      "location_planet_name": "Endor",
      "note": "Tracked through prior temporal mutations."
    }
  ]
}
```

## Events

### `POST /events`

Creates an event.

### `GET /events`

Lists events with timeline and semantic filters. This is the primary collection endpoint for timeline browsing; event-list filtering lives under `/events` rather than a separate `/timeline/events` namespace.

Query parameters:

- `start_year` optional integer
- `end_year` optional integer
- `era` optional string
- `character` optional character slug
- `location` optional planet slug
- `causal_depth` optional integer, range `1..8`
- `limit` optional, default `50`, range `1..200`
- `offset` optional, default `0`
- `order` optional `asc|desc`, default `asc`

### `GET /events/{event_id}`

Fetches a single event by id.

### `GET /events/by-slug/{slug}`

Fetches a single event by slug.

### `GET /events/{event_id}/dependencies`

Returns upstream causal dependencies for an event.

Query parameters:

- `depth` optional integer, range `1..8`

### `GET /events/{event_id}/consequences`

Returns downstream causal consequences for an event.

Query parameters:

- `depth` optional integer, range `1..8`

### `GET /events/{event_id}/causal-graph`

Returns an event-focused causal graph.

Query parameters:

- `depth` optional integer, default `2`, range `1..8`

### `GET /events/{event_id}/impact`

Returns impacted downstream events and broken edges for an event.

### `GET /events/{event_id}/universe-state`

Returns the projected universe state immediately before the selected event.

## Engine

### `GET /engine/simulate-break/{event_id}`

Runs the break-simulation engine for an event and returns the alternate branch graph with per-node statuses such as `broken`, `invalidated`, and `unresolved`.

## Characters

### `POST /characters`

Creates a character.

### `GET /characters`

Lists characters.

### `GET /characters/by-slug/{slug}`

Fetches a character by slug.

### `GET /characters/{character_id}/timeline`

Returns the filtered event timeline for a character.

Query parameters:

- `start_year` optional integer
- `end_year` optional integer
- `era` optional string
- `location` optional planet slug
- `causal_depth` optional integer, range `1..8`
- `limit` optional, default `50`, range `1..200`
- `offset` optional, default `0`
- `order` optional `asc|desc`, default `asc`

## Planets

### `POST /planets`

Creates a planet.

### `GET /planets`

Lists planets.

### `GET /planets/by-slug/{slug}`

Fetches a planet by slug.

## Factions

### `POST /factions`

Creates a faction.

### `GET /factions`

Lists factions.

### `GET /factions/by-slug/{slug}`

Fetches a faction by slug.

## Graph

### `POST /graph/relationships`

Creates a graph relationship or temporal mutation.

Used for:

- causal edges such as `CAUSES`
- archive semantics such as `INVOLVES`, `LOCATED_IN`, `MEMBER_OF`, `ALLIED_WITH`, and `ENEMY_OF`
- temporal mutations such as `SETS_ALIVE_STATE`, `SETS_CHARACTER_LOCATION`, `SETS_PLANET_CONTROL`, and `SETS_ARTIFACT_LOCATION`

Request payload fields:

- `type` relationship type
- `from_node_id` source node id
- `to_node_id` target node id
- `note` optional note
- `subject_node_id` optional subject entity for stateful mutations
- `artifact_key` optional artifact identifier for artifact-location mutations
- `value_bool` optional boolean payload, used by alive-state mutations
- `value_text` optional text payload

Validation behavior before commit:

- verifies that source and target nodes exist
- rejects self-referential relationships
- rejects unsupported source/target node type combinations
- rejects duplicate relationships
- rejects `CAUSES` edges that would introduce a cycle
- rejects `CAUSES` edges that violate chronology ordering
- normalizes canonical symmetric relationships such as `ALLIED_WITH` and `ENEMY_OF` to a stable endpoint order

This means structural checks for new relationship writes happen in the application layer before Neo4j persistence, while `scripts/audit/relationship_integrity.cypher` remains useful as a post-hoc audit for existing graph data.

## Notes

- All routes are mounted under `/api/v1`.
- The source of truth for request and response shapes is the FastAPI schema exposed at `/docs`.
- Traversal-heavy endpoints cap public depth arguments at `8`, and Neo4j reads are executed with an application-configured query timeout.
- Validation errors, missing entities, duplicate edges, unsupported relationships, and chronology violations are surfaced by the backend as HTTP errors through the API error handlers.
