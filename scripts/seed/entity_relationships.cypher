// ============================================================================
// Holocron-supported relationships for Character, Planet, and Faction nodes
// ============================================================================
//
// This script maps the inserted nodes onto the backend's supported
// relationship types and property conventions:
// - LOCATED_IN
// - MEMBER_OF
// - ALLIED_WITH
// - ENEMY_OF
//
// For event-scoped edges such as INVOLVES and Event -> LOCATED_IN, use the
// API or adapt the optional examples at the bottom to your event slugs.

// ============================================================================
// 1. CHARACTER -> PLANET
// ============================================================================

MATCH (c:Character {id: "char-anakin-skywalker"}), (p:Planet {id: "planet-tatooine"})
MERGE (c)-[r:LOCATED_IN {from_node_id: c.id, to_node_id: p.id}]->(p)
ON CREATE SET
  r.id = "located-in-char-anakin-skywalker-planet-tatooine",
  r.type = "LOCATED_IN",
  r.note = "Homeworld",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Homeworld",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-luke-skywalker"}), (p:Planet {id: "planet-tatooine"})
MERGE (c)-[r:LOCATED_IN {from_node_id: c.id, to_node_id: p.id}]->(p)
ON CREATE SET
  r.id = "located-in-char-luke-skywalker-planet-tatooine",
  r.type = "LOCATED_IN",
  r.note = "Homeworld",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Homeworld",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-sheev-palpatine"}), (p:Planet {id: "planet-naboo"})
MERGE (c)-[r:LOCATED_IN {from_node_id: c.id, to_node_id: p.id}]->(p)
ON CREATE SET
  r.id = "located-in-char-sheev-palpatine-planet-naboo",
  r.type = "LOCATED_IN",
  r.note = "Homeworld",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Homeworld",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-padme-amidala"}), (p:Planet {id: "planet-naboo"})
MERGE (c)-[r:LOCATED_IN {from_node_id: c.id, to_node_id: p.id}]->(p)
ON CREATE SET
  r.id = "located-in-char-padme-amidala-planet-naboo",
  r.type = "LOCATED_IN",
  r.note = "Homeworld",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Homeworld",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-leia-organa"}), (p:Planet {id: "planet-alderaan"})
MERGE (c)-[r:LOCATED_IN {from_node_id: c.id, to_node_id: p.id}]->(p)
ON CREATE SET
  r.id = "located-in-char-leia-organa-planet-alderaan",
  r.type = "LOCATED_IN",
  r.note = "Homeworld",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Homeworld",
  r.updated_at = datetime();

// ============================================================================
// 2. CHARACTER -> FACTION
// ============================================================================

MATCH (c:Character {id: "char-obi-wan-kenobi"}), (f:Faction {id: "faction-jedi-order"})
MERGE (c)-[r:MEMBER_OF {from_node_id: c.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "member-of-char-obi-wan-kenobi-faction-jedi-order",
  r.type = "MEMBER_OF",
  r.note = "historical",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "historical",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-obi-wan-kenobi"}), (f:Faction {id: "faction-galactic-republic"})
MERGE (c)-[r:MEMBER_OF {from_node_id: c.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "member-of-char-obi-wan-kenobi-faction-galactic-republic",
  r.type = "MEMBER_OF",
  r.note = "historical",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "historical",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-anakin-skywalker"}), (f:Faction {id: "faction-jedi-order"})
MERGE (c)-[r:MEMBER_OF {from_node_id: c.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "member-of-char-anakin-skywalker-faction-jedi-order",
  r.type = "MEMBER_OF",
  r.note = "betrayed",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "betrayed",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-anakin-skywalker"}), (f:Faction {id: "faction-galactic-empire"})
MERGE (c)-[r:MEMBER_OF {from_node_id: c.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "member-of-char-anakin-skywalker-faction-galactic-empire",
  r.type = "MEMBER_OF",
  r.note = "historical",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "historical",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-sheev-palpatine"}), (f:Faction {id: "faction-sith-order"})
MERGE (c)-[r:MEMBER_OF {from_node_id: c.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "member-of-char-sheev-palpatine-faction-sith-order",
  r.type = "MEMBER_OF",
  r.note = "leader",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "leader",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-sheev-palpatine"}), (f:Faction {id: "faction-galactic-empire"})
MERGE (c)-[r:MEMBER_OF {from_node_id: c.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "member-of-char-sheev-palpatine-faction-galactic-empire",
  r.type = "MEMBER_OF",
  r.note = "leader",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "leader",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-luke-skywalker"}), (f:Faction {id: "faction-rebel-alliance"})
MERGE (c)-[r:MEMBER_OF {from_node_id: c.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "member-of-char-luke-skywalker-faction-rebel-alliance",
  r.type = "MEMBER_OF",
  r.note = "active",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "active",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-luke-skywalker"}), (f:Faction {id: "faction-jedi-order"})
MERGE (c)-[r:MEMBER_OF {from_node_id: c.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "member-of-char-luke-skywalker-faction-jedi-order",
  r.type = "MEMBER_OF",
  r.note = "active",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "active",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-leia-organa"}), (f:Faction {id: "faction-rebel-alliance"})
MERGE (c)-[r:MEMBER_OF {from_node_id: c.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "member-of-char-leia-organa-faction-rebel-alliance",
  r.type = "MEMBER_OF",
  r.note = "historical",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "historical",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-leia-organa"}), (f:Faction {id: "faction-resistance"})
MERGE (c)-[r:MEMBER_OF {from_node_id: c.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "member-of-char-leia-organa-faction-resistance",
  r.type = "MEMBER_OF",
  r.note = "leader",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "leader",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-rey-skywalker"}), (f:Faction {id: "faction-resistance"})
MERGE (c)-[r:MEMBER_OF {from_node_id: c.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "member-of-char-rey-skywalker-faction-resistance",
  r.type = "MEMBER_OF",
  r.note = "active",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "active",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-rey-skywalker"}), (f:Faction {id: "faction-jedi-order"})
MERGE (c)-[r:MEMBER_OF {from_node_id: c.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "member-of-char-rey-skywalker-faction-jedi-order",
  r.type = "MEMBER_OF",
  r.note = "active",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "active",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-kylo-ren"}), (f:Faction {id: "faction-first-order"})
MERGE (c)-[r:MEMBER_OF {from_node_id: c.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "member-of-char-kylo-ren-faction-first-order",
  r.type = "MEMBER_OF",
  r.note = "historical",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "historical",
  r.updated_at = datetime();

MATCH (c:Character {id: "char-grand-moff-tarkin"}), (f:Faction {id: "faction-galactic-empire"})
MERGE (c)-[r:MEMBER_OF {from_node_id: c.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "member-of-char-grand-moff-tarkin-faction-galactic-empire",
  r.type = "MEMBER_OF",
  r.note = "historical",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "historical",
  r.updated_at = datetime();

// ============================================================================
// 3. FACTION <-> FACTION
// ============================================================================

MATCH (a:Faction {id: "faction-jedi-order"}), (b:Faction {id: "faction-galactic-republic"})
MERGE (a)-[r:ALLIED_WITH {from_node_id: a.id, to_node_id: b.id}]->(b)
ON CREATE SET
  r.id = "allied-with-faction-jedi-order-faction-galactic-republic",
  r.type = "ALLIED_WITH",
  r.note = "Institutional alliance during the Republic era",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Institutional alliance during the Republic era",
  r.updated_at = datetime();

MATCH (a:Faction {id: "faction-rebel-alliance"}), (b:Faction {id: "faction-resistance"})
MERGE (a)-[r:ALLIED_WITH {from_node_id: a.id, to_node_id: b.id}]->(b)
ON CREATE SET
  r.id = "allied-with-faction-rebel-alliance-faction-resistance",
  r.type = "ALLIED_WITH",
  r.note = "Shared anti-authoritarian cause across eras",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Shared anti-authoritarian cause across eras",
  r.updated_at = datetime();

MATCH (a:Faction {id: "faction-sith-order"}), (b:Faction {id: "faction-galactic-empire"})
MERGE (a)-[r:ALLIED_WITH {from_node_id: a.id, to_node_id: b.id}]->(b)
ON CREATE SET
  r.id = "allied-with-faction-sith-order-faction-galactic-empire",
  r.type = "ALLIED_WITH",
  r.note = "Imperial power built under Sith control",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Imperial power built under Sith control",
  r.updated_at = datetime();

MATCH (a:Faction {id: "faction-cis"}), (b:Faction {id: "faction-galactic-republic"})
MERGE (a)-[r:ENEMY_OF {from_node_id: a.id, to_node_id: b.id}]->(b)
ON CREATE SET
  r.id = "enemy-of-faction-cis-faction-galactic-republic",
  r.type = "ENEMY_OF",
  r.note = "Clone Wars belligerents",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Clone Wars belligerents",
  r.updated_at = datetime();

MATCH (a:Faction {id: "faction-galactic-empire"}), (b:Faction {id: "faction-rebel-alliance"})
MERGE (a)-[r:ENEMY_OF {from_node_id: a.id, to_node_id: b.id}]->(b)
ON CREATE SET
  r.id = "enemy-of-faction-galactic-empire-faction-rebel-alliance",
  r.type = "ENEMY_OF",
  r.note = "Galactic Civil War belligerents",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Galactic Civil War belligerents",
  r.updated_at = datetime();

MATCH (a:Faction {id: "faction-first-order"}), (b:Faction {id: "faction-resistance"})
MERGE (a)-[r:ENEMY_OF {from_node_id: a.id, to_node_id: b.id}]->(b)
ON CREATE SET
  r.id = "enemy-of-faction-first-order-faction-resistance",
  r.type = "ENEMY_OF",
  r.note = "Sequel-era belligerents",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Sequel-era belligerents",
  r.updated_at = datetime();

// ============================================================================
// 4. OPTIONAL EVENT RELATIONSHIPS
// ============================================================================
//
// Uncomment and adapt these if your Event slugs differ. The backend supports:
// - (:Event)-[:INVOLVES]->(:Character|:Faction)
// - (:Event)-[:LOCATED_IN]->(:Planet)
//
// MATCH (e:Event {slug: "order-66"}), (c:Character {id: "char-anakin-skywalker"})
// MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
// ON CREATE SET
//   r.id = "involves-order-66-char-anakin-skywalker",
//   r.type = "INVOLVES",
//   r.note = "Primary participant",
//   r.created_at = datetime(),
//   r.updated_at = datetime()
// ON MATCH SET
//   r.note = "Primary participant",
//   r.updated_at = datetime();
//
// MATCH (e:Event {slug: "order-66"}), (p:Planet {id: "planet-coruscant"})
// MERGE (e)-[r:LOCATED_IN {from_node_id: e.id, to_node_id: p.id}]->(p)
// ON CREATE SET
//   r.id = "located-in-order-66-planet-coruscant",
//   r.type = "LOCATED_IN",
//   r.note = "Primary setting",
//   r.created_at = datetime(),
//   r.updated_at = datetime()
// ON MATCH SET
//   r.note = "Primary setting",
//   r.updated_at = datetime();
