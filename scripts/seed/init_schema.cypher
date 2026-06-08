CREATE CONSTRAINT event_id_unique IF NOT EXISTS
FOR (e:Event)
REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT event_slug_unique IF NOT EXISTS
FOR (e:Event)
REQUIRE e.slug IS UNIQUE;

CREATE CONSTRAINT character_id_unique IF NOT EXISTS
FOR (c:Character)
REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT character_slug_unique IF NOT EXISTS
FOR (c:Character)
REQUIRE c.slug IS UNIQUE;

CREATE CONSTRAINT planet_id_unique IF NOT EXISTS
FOR (p:Planet)
REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT planet_slug_unique IF NOT EXISTS
FOR (p:Planet)
REQUIRE p.slug IS UNIQUE;

CREATE CONSTRAINT faction_id_unique IF NOT EXISTS
FOR (f:Faction)
REQUIRE f.id IS UNIQUE;

CREATE CONSTRAINT faction_slug_unique IF NOT EXISTS
FOR (f:Faction)
REQUIRE f.slug IS UNIQUE;

CREATE INDEX event_start_year_index IF NOT EXISTS
FOR (e:Event)
ON (e.start_year);

CREATE INDEX event_title_index IF NOT EXISTS
FOR (e:Event)
ON (e.title);

CREATE INDEX character_name_index IF NOT EXISTS
FOR (c:Character)
ON (c.name);

CREATE INDEX planet_name_index IF NOT EXISTS
FOR (p:Planet)
ON (p.name);

CREATE INDEX faction_name_index IF NOT EXISTS
FOR (f:Faction)
ON (f.name);

