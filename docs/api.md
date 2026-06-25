# API

Base URL: `http://localhost:8000/api/v1`

Interactive docs:

- Swagger UI: `http://localhost:8000/docs`

Companion docs:

- Example requests and payloads: [api-examples.md](api-examples.md)
- Broader system context: [engineering-design.md](engineering-design.md)

## Conventions

- All routes are mounted under `/api/v1`.
- Exact request and response schemas live in the OpenAPI document at `/docs`.
- Traversal-heavy endpoints cap public depth at `8`.
- Event dependency and consequence list endpoints interpret `depth` as an exact hop distance.

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
- `GET /events/{event_id}/dependencies`
- `GET /events/{event_id}/consequences`
- `GET /events/{event_id}/causal-graph`
- `GET /events/{event_id}/impact`
- `GET /events/{event_id}/universe-state`

### Engine

- `GET /engine/simulate-break/{event_id}`

### Characters

- `POST /characters`
- `GET /characters`
- `GET /characters/by-slug/{slug}`
- `GET /characters/{character_id}/timeline`

### Planets

- `POST /planets`
- `GET /planets`
- `GET /planets/by-slug/{slug}`

### Factions

- `POST /factions`
- `GET /factions`
- `GET /factions/by-slug/{slug}`
- `GET /factions/by-slug/{slug}/detail`

### Graph

- `POST /graph/relationships`

## Endpoint Reference

### Health

#### `GET /health`

Returns a simple status payload.

### Search

#### `GET /search`

Searches events, characters, planets, and factions.

Query params:

- `q` required search string, minimum length `1`
- `limit` optional, default `10`, range `1..25`

### Events

#### `POST /events`

Creates an event.

#### `GET /events`

Lists events for the timeline page and filtered archive views.

Query params:

- `start_year` optional integer
- `end_year` optional integer
- `era` optional string
- `character` optional character slug
- `location` optional planet slug
- `causal_depth` optional integer, range `1..8`
- `limit` optional, default `50`, range `1..200`
- `offset` optional, default `0`
- `order` optional `asc|desc`, default `asc`

#### `GET /events/{event_id}`

Fetches a single event by backend id.

#### `GET /events/by-slug/{slug}`

Fetches a single event by slug for frontend routing.

#### `GET /events/{event_id}/dependencies`

Returns upstream events at the requested hop distance.

Query params:

- `depth` optional integer, range `1..8`, interpreted as exact hop distance

#### `GET /events/{event_id}/consequences`

Returns downstream events at the requested hop distance.

Query params:

- `depth` optional integer, range `1..8`, interpreted as exact hop distance

#### `GET /events/{event_id}/causal-graph`

Returns the focus event plus the connected causal subgraph within the requested depth.

Query params:

- `depth` optional integer, default `2`, range `1..8`

#### `GET /events/{event_id}/impact`

Returns downstream events affected by removing this event, plus the broken edges.

#### `GET /events/{event_id}/universe-state`

Replays prior mutations and returns the world state immediately before the selected event.

### Engine

#### `GET /engine/simulate-break/{event_id}`

Removes one event, walks the downstream branch, and returns per-node statuses like `broken`, `invalidated`, and `unresolved`.

### Characters

#### `POST /characters`

Creates a character.

#### `GET /characters`

Lists characters.

#### `GET /characters/by-slug/{slug}`

Fetches a character by slug.

#### `GET /characters/{character_id}/timeline`

Returns events linked to the character, with the same timeline filters used on `/events`.

Query params:

- `start_year` optional integer
- `end_year` optional integer
- `era` optional string
- `location` optional planet slug
- `causal_depth` optional integer, range `1..8`
- `limit` optional, default `50`, range `1..200`
- `offset` optional, default `0`
- `order` optional `asc|desc`, default `asc`

### Planets

#### `POST /planets`

Creates a planet.

#### `GET /planets`

Lists planets.

#### `GET /planets/by-slug/{slug}`

Fetches a planet by slug.

### Factions

#### `POST /factions`

Creates a faction.

#### `GET /factions`

Lists factions.

#### `GET /factions/by-slug/{slug}`

Fetches a faction by slug.

#### `GET /factions/by-slug/{slug}/detail`

Returns the aggregate payload used by the faction detail page.

Response includes:

- `faction` base faction record
- `characters` characters associated through faction-tagged events
- `enemy_factions` factions connected through `ENEMY_OF`
- `involved_events` events tagged through `INVOLVES`

### Graph

#### `POST /graph/relationships`

Creates a graph relationship or a temporal mutation.

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

Validation before commit:

- verifies that source and target nodes exist
- rejects self-referential relationships
- rejects unsupported source/target node type combinations
- rejects duplicate relationships
- rejects `CAUSES` edges that would introduce a cycle
- rejects `CAUSES` edges that violate chronology ordering
- canonicalizes symmetric relationships such as `ALLIED_WITH` and `ENEMY_OF` so duplicate checks are stable
