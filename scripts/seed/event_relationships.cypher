// ============================================================================
// Event relationships for the current Holocron dataset
// ============================================================================
//
// Uses the Event ids/slugs currently present in Neo4j and links them to the
// existing Character, Planet, and Faction nodes with Holocron-supported edges:
// - INVOLVES
// - LOCATED_IN
//
// Safe to rerun because each edge is created with MERGE on the backend's
// identifying relationship properties.

// ============================================================================
// Helper pattern
// ============================================================================
// Relationship properties follow the backend convention:
// - from_node_id
// - to_node_id
// - id
// - type
// - note
// - created_at
// - updated_at

// ============================================================================
// The Great Disaster
// ============================================================================

MATCH (e:Event {id: "event-great-disaster"}), (f:Faction {id: "faction-jedi-order"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-great-disaster-faction-jedi-order",
  r.type = "INVOLVES",
  r.note = "Jedi response to the disaster",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Jedi response to the disaster",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-great-disaster"}), (f:Faction {id: "faction-galactic-republic"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-great-disaster-faction-galactic-republic",
  r.type = "INVOLVES",
  r.note = "Republic emergency response",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Republic emergency response",
  r.updated_at = datetime();

// ============================================================================
// Destruction of Starlight Beacon
// ============================================================================

MATCH (e:Event {id: "event-destruction-starlight"}), (f:Faction {id: "faction-jedi-order"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-destruction-starlight-faction-jedi-order",
  r.type = "INVOLVES",
  r.note = "Jedi defenders and responders",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Jedi defenders and responders",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-destruction-starlight"}), (f:Faction {id: "faction-galactic-republic"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-destruction-starlight-faction-galactic-republic",
  r.type = "INVOLVES",
  r.note = "Republic station and relief effort",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Republic station and relief effort",
  r.updated_at = datetime();

// ============================================================================
// Invasion of Naboo
// ============================================================================

MATCH (e:Event {id: "event-invasion-naboo"}), (p:Planet {id: "planet-naboo"})
MERGE (e)-[r:LOCATED_IN {from_node_id: e.id, to_node_id: p.id}]->(p)
ON CREATE SET
  r.id = "located-in-event-invasion-naboo-planet-naboo",
  r.type = "LOCATED_IN",
  r.note = "Primary setting",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Primary setting",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-invasion-naboo"}), (c:Character {id: "char-padme-amidala"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-invasion-naboo-char-padme-amidala",
  r.type = "INVOLVES",
  r.note = "Queen of Naboo",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Queen of Naboo",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-invasion-naboo"}), (c:Character {id: "char-sheev-palpatine"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-invasion-naboo-char-sheev-palpatine",
  r.type = "INVOLVES",
  r.note = "Political architect behind the crisis",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Political architect behind the crisis",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-invasion-naboo"}), (f:Faction {id: "faction-galactic-republic"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-invasion-naboo-faction-galactic-republic",
  r.type = "INVOLVES",
  r.note = "Senate and Republic political response",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Senate and Republic political response",
  r.updated_at = datetime();

// ============================================================================
// Battle of Geonosis
// ============================================================================

MATCH (e:Event {id: "event-battle-geonosis"}), (p:Planet {id: "planet-geonosis"})
MERGE (e)-[r:LOCATED_IN {from_node_id: e.id, to_node_id: p.id}]->(p)
ON CREATE SET
  r.id = "located-in-event-battle-geonosis-planet-geonosis",
  r.type = "LOCATED_IN",
  r.note = "Primary setting",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Primary setting",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-geonosis"}), (c:Character {id: "char-anakin-skywalker"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-geonosis-char-anakin-skywalker",
  r.type = "INVOLVES",
  r.note = "Republic combatant",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Republic combatant",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-geonosis"}), (c:Character {id: "char-obi-wan-kenobi"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-geonosis-char-obi-wan-kenobi",
  r.type = "INVOLVES",
  r.note = "Republic combatant",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Republic combatant",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-geonosis"}), (f:Faction {id: "faction-galactic-republic"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-geonosis-faction-galactic-republic",
  r.type = "INVOLVES",
  r.note = "Republic military intervention",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Republic military intervention",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-geonosis"}), (f:Faction {id: "faction-cis"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-geonosis-faction-cis",
  r.type = "INVOLVES",
  r.note = "Separatist belligerent",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Separatist belligerent",
  r.updated_at = datetime();

// ============================================================================
// Malevolence Campaign
// ============================================================================

MATCH (e:Event {id: "event-malevolence-campaign"}), (c:Character {id: "char-anakin-skywalker"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-malevolence-campaign-char-anakin-skywalker",
  r.type = "INVOLVES",
  r.note = "Republic strike participant",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Republic strike participant",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-malevolence-campaign"}), (c:Character {id: "char-obi-wan-kenobi"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-malevolence-campaign-char-obi-wan-kenobi",
  r.type = "INVOLVES",
  r.note = "Republic strike participant",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Republic strike participant",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-malevolence-campaign"}), (f:Faction {id: "faction-galactic-republic"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-malevolence-campaign-faction-galactic-republic",
  r.type = "INVOLVES",
  r.note = "Republic naval response",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Republic naval response",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-malevolence-campaign"}), (f:Faction {id: "faction-cis"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-malevolence-campaign-faction-cis",
  r.type = "INVOLVES",
  r.note = "Separatist naval offensive",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Separatist naval offensive",
  r.updated_at = datetime();

// ============================================================================
// Execution of Order 66
// ============================================================================

MATCH (e:Event {id: "event-order-66"}), (p:Planet {id: "planet-coruscant"})
MERGE (e)-[r:LOCATED_IN {from_node_id: e.id, to_node_id: p.id}]->(p)
ON CREATE SET
  r.id = "located-in-event-order-66-planet-coruscant",
  r.type = "LOCATED_IN",
  r.note = "Central political setting",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Central political setting",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-order-66"}), (c:Character {id: "char-anakin-skywalker"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-order-66-char-anakin-skywalker",
  r.type = "INVOLVES",
  r.note = "Executor of the purge",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Executor of the purge",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-order-66"}), (c:Character {id: "char-obi-wan-kenobi"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-order-66-char-obi-wan-kenobi",
  r.type = "INVOLVES",
  r.note = "Surviving Jedi leader",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Surviving Jedi leader",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-order-66"}), (c:Character {id: "char-sheev-palpatine"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-order-66-char-sheev-palpatine",
  r.type = "INVOLVES",
  r.note = "Issued the order",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Issued the order",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-order-66"}), (f:Faction {id: "faction-jedi-order"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-order-66-faction-jedi-order",
  r.type = "INVOLVES",
  r.note = "Primary target of the purge",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Primary target of the purge",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-order-66"}), (f:Faction {id: "faction-galactic-republic"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-order-66-faction-galactic-republic",
  r.type = "INVOLVES",
  r.note = "Republic military structure enforces the order",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Republic military structure enforces the order",
  r.updated_at = datetime();

// ============================================================================
// Rise of the Empire
// ============================================================================

MATCH (e:Event {id: "event-rise-empire"}), (p:Planet {id: "planet-coruscant"})
MERGE (e)-[r:LOCATED_IN {from_node_id: e.id, to_node_id: p.id}]->(p)
ON CREATE SET
  r.id = "located-in-event-rise-empire-planet-coruscant",
  r.type = "LOCATED_IN",
  r.note = "Imperial proclamation on Coruscant",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Imperial proclamation on Coruscant",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-rise-empire"}), (c:Character {id: "char-anakin-skywalker"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-rise-empire-char-anakin-skywalker",
  r.type = "INVOLVES",
  r.note = "Enforcer of the new regime",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Enforcer of the new regime",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-rise-empire"}), (c:Character {id: "char-sheev-palpatine"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-rise-empire-char-sheev-palpatine",
  r.type = "INVOLVES",
  r.note = "Founder of the Empire",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Founder of the Empire",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-rise-empire"}), (f:Faction {id: "faction-galactic-republic"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-rise-empire-faction-galactic-republic",
  r.type = "INVOLVES",
  r.note = "State replaced by the Empire",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "State replaced by the Empire",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-rise-empire"}), (f:Faction {id: "faction-galactic-empire"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-rise-empire-faction-galactic-empire",
  r.type = "INVOLVES",
  r.note = "New ruling regime",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "New ruling regime",
  r.updated_at = datetime();

// ============================================================================
// Siege of Mandalore
// ============================================================================

MATCH (e:Event {id: "event-siege-mandalore"}), (c:Character {id: "char-ahsoka-tano"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-siege-mandalore-char-ahsoka-tano",
  r.type = "INVOLVES",
  r.note = "Key field leader",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Key field leader",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-siege-mandalore"}), (c:Character {id: "char-anakin-skywalker"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-siege-mandalore-char-anakin-skywalker",
  r.type = "INVOLVES",
  r.note = "Indirectly tied through the final Clone Wars campaign",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Indirectly tied through the final Clone Wars campaign",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-siege-mandalore"}), (f:Faction {id: "faction-galactic-republic"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-siege-mandalore-faction-galactic-republic",
  r.type = "INVOLVES",
  r.note = "Republic-led operation",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Republic-led operation",
  r.updated_at = datetime();

// ============================================================================
// Ghorman Massacre
// ============================================================================

MATCH (e:Event {id: "event-ghorman-massacre"}), (f:Faction {id: "faction-galactic-empire"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-ghorman-massacre-faction-galactic-empire",
  r.type = "INVOLVES",
  r.note = "Imperial perpetrators",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Imperial perpetrators",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-ghorman-massacre"}), (f:Faction {id: "faction-rebel-alliance"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-ghorman-massacre-faction-rebel-alliance",
  r.type = "INVOLVES",
  r.note = "Galvanized anti-Imperial resistance",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Galvanized anti-Imperial resistance",
  r.updated_at = datetime();

// ============================================================================
// Battle of Atollon
// ============================================================================

MATCH (e:Event {id: "event-battle-atollon"}), (c:Character {id: "char-ahsoka-tano"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-atollon-char-ahsoka-tano",
  r.type = "INVOLVES",
  r.note = "Rebel operative connected to the campaign",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Rebel operative connected to the campaign",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-atollon"}), (f:Faction {id: "faction-rebel-alliance"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-atollon-faction-rebel-alliance",
  r.type = "INVOLVES",
  r.note = "Rebel force under attack",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Rebel force under attack",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-atollon"}), (f:Faction {id: "faction-galactic-empire"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-atollon-faction-galactic-empire",
  r.type = "INVOLVES",
  r.note = "Imperial offensive",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Imperial offensive",
  r.updated_at = datetime();

// ============================================================================
// Battle of Scarif
// ============================================================================

MATCH (e:Event {id: "event-battle-scarif"}), (c:Character {id: "char-grand-moff-tarkin"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-scarif-char-grand-moff-tarkin",
  r.type = "INVOLVES",
  r.note = "Imperial high command involvement",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Imperial high command involvement",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-scarif"}), (f:Faction {id: "faction-rebel-alliance"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-scarif-faction-rebel-alliance",
  r.type = "INVOLVES",
  r.note = "Rebel assault force",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Rebel assault force",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-scarif"}), (f:Faction {id: "faction-galactic-empire"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-scarif-faction-galactic-empire",
  r.type = "INVOLVES",
  r.note = "Imperial defenders",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Imperial defenders",
  r.updated_at = datetime();

// ============================================================================
// Battle of Yavin
// ============================================================================

MATCH (e:Event {id: "event-battle-yavin"}), (c:Character {id: "char-luke-skywalker"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-yavin-char-luke-skywalker",
  r.type = "INVOLVES",
  r.note = "Rebel pilot in the trench run",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Rebel pilot in the trench run",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-yavin"}), (c:Character {id: "char-leia-organa"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-yavin-char-leia-organa",
  r.type = "INVOLVES",
  r.note = "Rebel leadership",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Rebel leadership",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-yavin"}), (c:Character {id: "char-grand-moff-tarkin"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-yavin-char-grand-moff-tarkin",
  r.type = "INVOLVES",
  r.note = "Imperial command",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Imperial command",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-yavin"}), (f:Faction {id: "faction-rebel-alliance"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-yavin-faction-rebel-alliance",
  r.type = "INVOLVES",
  r.note = "Rebel victory",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Rebel victory",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-yavin"}), (f:Faction {id: "faction-galactic-empire"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-yavin-faction-galactic-empire",
  r.type = "INVOLVES",
  r.note = "Imperial defeat",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Imperial defeat",
  r.updated_at = datetime();

// ============================================================================
// Battle of Hoth
// ============================================================================

MATCH (e:Event {id: "event-battle-hoth"}), (p:Planet {id: "planet-hoth"})
MERGE (e)-[r:LOCATED_IN {from_node_id: e.id, to_node_id: p.id}]->(p)
ON CREATE SET
  r.id = "located-in-event-battle-hoth-planet-hoth",
  r.type = "LOCATED_IN",
  r.note = "Primary setting",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Primary setting",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-hoth"}), (c:Character {id: "char-luke-skywalker"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-hoth-char-luke-skywalker",
  r.type = "INVOLVES",
  r.note = "Rebel combatant",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Rebel combatant",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-hoth"}), (c:Character {id: "char-leia-organa"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-hoth-char-leia-organa",
  r.type = "INVOLVES",
  r.note = "Rebel command",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Rebel command",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-hoth"}), (f:Faction {id: "faction-rebel-alliance"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-hoth-faction-rebel-alliance",
  r.type = "INVOLVES",
  r.note = "Defending force",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Defending force",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-hoth"}), (f:Faction {id: "faction-galactic-empire"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-hoth-faction-galactic-empire",
  r.type = "INVOLVES",
  r.note = "Attacking force",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Attacking force",
  r.updated_at = datetime();

// ============================================================================
// Battle of Endor
// ============================================================================

MATCH (e:Event {id: "event-battle-endor"}), (p:Planet {id: "planet-endor"})
MERGE (e)-[r:LOCATED_IN {from_node_id: e.id, to_node_id: p.id}]->(p)
ON CREATE SET
  r.id = "located-in-event-battle-endor-planet-endor",
  r.type = "LOCATED_IN",
  r.note = "Primary setting",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Primary setting",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-endor"}), (c:Character {id: "char-luke-skywalker"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-endor-char-luke-skywalker",
  r.type = "INVOLVES",
  r.note = "Jedi participant",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Jedi participant",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-endor"}), (c:Character {id: "char-leia-organa"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-endor-char-leia-organa",
  r.type = "INVOLVES",
  r.note = "Rebel participant",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Rebel participant",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-endor"}), (f:Faction {id: "faction-rebel-alliance"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-endor-faction-rebel-alliance",
  r.type = "INVOLVES",
  r.note = "Rebel strike force",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Rebel strike force",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-endor"}), (f:Faction {id: "faction-galactic-empire"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-endor-faction-galactic-empire",
  r.type = "INVOLVES",
  r.note = "Imperial defending force",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Imperial defending force",
  r.updated_at = datetime();

// ============================================================================
// Battle of Jakku
// ============================================================================

MATCH (e:Event {id: "event-battle-jakku"}), (f:Faction {id: "faction-rebel-alliance"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-jakku-faction-rebel-alliance",
  r.type = "INVOLVES",
  r.note = "New Republic-aligned victors",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "New Republic-aligned victors",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-jakku"}), (f:Faction {id: "faction-galactic-empire"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-jakku-faction-galactic-empire",
  r.type = "INVOLVES",
  r.note = "Imperial remnant defeat",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Imperial remnant defeat",
  r.updated_at = datetime();

// ============================================================================
// Destruction of Luke's Jedi Temple
// ============================================================================

MATCH (e:Event {id: "event-destruction-jedi-praxeum"}), (c:Character {id: "char-luke-skywalker"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-destruction-jedi-praxeum-char-luke-skywalker",
  r.type = "INVOLVES",
  r.note = "Temple founder",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Temple founder",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-destruction-jedi-praxeum"}), (c:Character {id: "char-kylo-ren"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-destruction-jedi-praxeum-char-kylo-ren",
  r.type = "INVOLVES",
  r.note = "Temple destroyer",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Temple destroyer",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-destruction-jedi-praxeum"}), (f:Faction {id: "faction-jedi-order"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-destruction-jedi-praxeum-faction-jedi-order",
  r.type = "INVOLVES",
  r.note = "Jedi legacy destroyed",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Jedi legacy destroyed",
  r.updated_at = datetime();

// ============================================================================
// Battle of Crait
// ============================================================================

MATCH (e:Event {id: "event-battle-crait"}), (c:Character {id: "char-luke-skywalker"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-crait-char-luke-skywalker",
  r.type = "INVOLVES",
  r.note = "Legendary intervention",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Legendary intervention",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-crait"}), (c:Character {id: "char-leia-organa"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-crait-char-leia-organa",
  r.type = "INVOLVES",
  r.note = "Resistance leadership",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Resistance leadership",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-crait"}), (c:Character {id: "char-kylo-ren"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-crait-char-kylo-ren",
  r.type = "INVOLVES",
  r.note = "First Order commander",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "First Order commander",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-crait"}), (f:Faction {id: "faction-resistance"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-crait-faction-resistance",
  r.type = "INVOLVES",
  r.note = "Defending survivors",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Defending survivors",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-crait"}), (f:Faction {id: "faction-first-order"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-crait-faction-first-order",
  r.type = "INVOLVES",
  r.note = "Attacking force",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Attacking force",
  r.updated_at = datetime();

// ============================================================================
// Battle of D'Qar
// ============================================================================

MATCH (e:Event {id: "event-battle-dqar"}), (c:Character {id: "char-leia-organa"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-dqar-char-leia-organa",
  r.type = "INVOLVES",
  r.note = "Resistance leadership",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Resistance leadership",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-dqar"}), (c:Character {id: "char-kylo-ren"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-dqar-char-kylo-ren",
  r.type = "INVOLVES",
  r.note = "First Order attacker",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "First Order attacker",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-dqar"}), (f:Faction {id: "faction-resistance"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-dqar-faction-resistance",
  r.type = "INVOLVES",
  r.note = "Evacuating defenders",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Evacuating defenders",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-dqar"}), (f:Faction {id: "faction-first-order"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-dqar-faction-first-order",
  r.type = "INVOLVES",
  r.note = "Attacking force",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Attacking force",
  r.updated_at = datetime();

// ============================================================================
// Hosnian Cataclysm
// ============================================================================

MATCH (e:Event {id: "event-hosnian-cataclysm"}), (f:Faction {id: "faction-first-order"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-hosnian-cataclysm-faction-first-order",
  r.type = "INVOLVES",
  r.note = "Perpetrating regime",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Perpetrating regime",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-hosnian-cataclysm"}), (f:Faction {id: "faction-resistance"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-hosnian-cataclysm-faction-resistance",
  r.type = "INVOLVES",
  r.note = "Escalates the Resistance war effort",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Escalates the Resistance war effort",
  r.updated_at = datetime();

// ============================================================================
// Battle of Exegol
// ============================================================================

MATCH (e:Event {id: "event-battle-exegol"}), (p:Planet {id: "planet-exegol"})
MERGE (e)-[r:LOCATED_IN {from_node_id: e.id, to_node_id: p.id}]->(p)
ON CREATE SET
  r.id = "located-in-event-battle-exegol-planet-exegol",
  r.type = "LOCATED_IN",
  r.note = "Primary setting",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Primary setting",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-exegol"}), (c:Character {id: "char-rey-skywalker"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-exegol-char-rey-skywalker",
  r.type = "INVOLVES",
  r.note = "Jedi protagonist",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Jedi protagonist",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-exegol"}), (c:Character {id: "char-kylo-ren"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-exegol-char-kylo-ren",
  r.type = "INVOLVES",
  r.note = "Redeemed ally in the final battle",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Redeemed ally in the final battle",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-exegol"}), (c:Character {id: "char-sheev-palpatine"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: c.id}]->(c)
ON CREATE SET
  r.id = "involves-event-battle-exegol-char-sheev-palpatine",
  r.type = "INVOLVES",
  r.note = "Final antagonist",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Final antagonist",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-exegol"}), (f:Faction {id: "faction-resistance"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-exegol-faction-resistance",
  r.type = "INVOLVES",
  r.note = "Resistance-led victory",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Resistance-led victory",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-exegol"}), (f:Faction {id: "faction-first-order"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-exegol-faction-first-order",
  r.type = "INVOLVES",
  r.note = "First Order-aligned forces",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "First Order-aligned forces",
  r.updated_at = datetime();

MATCH (e:Event {id: "event-battle-exegol"}), (f:Faction {id: "faction-sith-order"})
MERGE (e)-[r:INVOLVES {from_node_id: e.id, to_node_id: f.id}]->(f)
ON CREATE SET
  r.id = "involves-event-battle-exegol-faction-sith-order",
  r.type = "INVOLVES",
  r.note = "Sith cult and legacy involvement",
  r.created_at = datetime(),
  r.updated_at = datetime()
ON MATCH SET
  r.note = "Sith cult and legacy involvement",
  r.updated_at = datetime();
