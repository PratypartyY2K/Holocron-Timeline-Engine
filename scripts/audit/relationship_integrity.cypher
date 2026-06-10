// Relationship integrity audit for Holocron Timeline Engine.
//
// Run these queries in Neo4j Browser or cypher-shell after loading your dataset.
// Each section returns only violations.

// 1. Self-referential relationships.
MATCH (source)-[r]->(source)
RETURN
  type(r) AS relationship_type,
  source.id AS node_id,
  labels(source) AS node_labels,
  properties(r) AS relationship
ORDER BY relationship_type, node_id;


// 2. Duplicate relationships by type and canonical endpoint pair.
MATCH (source)-[r]->(target)
WITH
  type(r) AS relationship_type,
  r.from_node_id AS from_node_id,
  r.to_node_id AS to_node_id,
  collect(properties(r)) AS relationships,
  count(*) AS duplicate_count
WHERE duplicate_count > 1
RETURN
  relationship_type,
  from_node_id,
  to_node_id,
  duplicate_count,
  relationships
ORDER BY duplicate_count DESC, relationship_type, from_node_id, to_node_id;


// 3. Relationship type does not match the allowed node-label pair.
MATCH (source)-[r]->(target)
WITH
  source,
  target,
  r,
  type(r) AS relationship_type,
  labels(source) AS source_labels,
  labels(target) AS target_labels
WHERE NOT (
  (relationship_type = 'CAUSES' AND 'Event' IN source_labels AND 'Event' IN target_labels) OR
  (
    relationship_type = 'INVOLVES' AND
    'Event' IN source_labels AND
    ('Character' IN target_labels OR 'Faction' IN target_labels)
  ) OR
  (
    relationship_type = 'LOCATED_IN' AND (
      ('Event' IN source_labels AND 'Planet' IN target_labels) OR
      ('Character' IN source_labels AND 'Planet' IN target_labels)
    )
  ) OR
  (relationship_type = 'MEMBER_OF' AND 'Character' IN source_labels AND 'Faction' IN target_labels) OR
  (relationship_type = 'ALLIED_WITH' AND 'Faction' IN source_labels AND 'Faction' IN target_labels) OR
  (relationship_type = 'ENEMY_OF' AND 'Faction' IN source_labels AND 'Faction' IN target_labels)
)
RETURN
  relationship_type,
  source.id AS source_id,
  source_labels,
  target.id AS target_id,
  target_labels,
  properties(r) AS relationship
ORDER BY relationship_type, source_id, target_id;


// 4. Symmetric faction relationships that are stored in non-canonical order.
MATCH (source:Faction)-[r]->(target:Faction)
WHERE type(r) IN ['ALLIED_WITH', 'ENEMY_OF']
  AND source.id = r.from_node_id
  AND target.id = r.to_node_id
  AND r.from_node_id > r.to_node_id
RETURN
  type(r) AS relationship_type,
  r.from_node_id AS from_node_id,
  r.to_node_id AS to_node_id,
  properties(r) AS relationship
ORDER BY relationship_type, from_node_id, to_node_id;
