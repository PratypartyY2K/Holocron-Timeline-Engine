# API Examples

Base URL: `http://localhost:8000/api/v1`

Use this file for concrete request and response examples. The compact reference lives in [api.md](api.md).

## Example 1: List timeline events with filters

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

## Example 2: Simulate a causal break

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

## Example 3: Read projected universe state before an event

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
