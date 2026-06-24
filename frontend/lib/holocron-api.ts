import { getApiBaseUrl } from "./api-base-url";

export type EventRecord = {
  id: string;
  slug: string;
  title: string;
  description: string | null;
  start_year: number;
  end_year: number | null;
  era: string | null;
  canon_status: string | null;
  dependency_count: number;
  centrality_score: number;
  source_refs: string[];
  faction_slugs: string[];
  faction_names: string[];
  created_at: string;
  updated_at: string;
};

export type CharacterRecord = {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  species: string | null;
  homeworld_name: string | null;
  created_at: string;
  updated_at: string;
};

export type PlanetRecord = {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  region: string | null;
  created_at: string;
  updated_at: string;
};

export type FactionRecord = {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type FactionDetailResponse = {
  faction: FactionRecord;
  characters: CharacterRecord[];
  enemy_factions: FactionRecord[];
  involved_events: EventRecord[];
};

export type EventListResponse = {
  items: EventRecord[];
  total: number;
  limit: number;
  offset: number;
};

export type CausalGraphEdgeRecord = {
  id: string;
  source_id: string;
  target_id: string;
  type: "CAUSES";
  note: string | null;
};

export type CausalGraphResponse = {
  focus_event_id: string;
  depth: number;
  nodes: EventRecord[];
  edges: CausalGraphEdgeRecord[];
};

export type EventImpactResponse = {
  event_id: string;
  impacted_events: EventRecord[];
  broken_edges: CausalGraphEdgeRecord[];
};

export type TimelineBreakSimulationNodeRecord = EventRecord & {
  status: "active" | "broken" | "invalidated" | "unresolved";
  topological_rank: number;
  affected_by_event_ids: string[];
  surviving_dependency_count: number;
  broken_dependency_count: number;
  unresolved_dependency_count: number;
};

export type TimelineBreakSimulationResponse = {
  broken_event_id: string;
  nodes: TimelineBreakSimulationNodeRecord[];
  edges: CausalGraphEdgeRecord[];
  topological_order: string[];
};

export type UniverseCharacterStateRecord = {
  id: string;
  slug: string;
  name: string;
  is_alive: boolean;
  location_planet_slug: string | null;
  location_planet_name: string | null;
};

export type FactionControlStateRecord = {
  planet_slug: string;
  planet_name: string;
  faction_slug: string;
  faction_name: string;
};

export type ArtifactLocationStateRecord = {
  artifact_key: string;
  artifact_name: string;
  holder_character_slug: string | null;
  holder_character_name: string | null;
  location_planet_slug: string | null;
  location_planet_name: string | null;
  note: string | null;
};

export type UniverseStateResponse = {
  event_id: string;
  event_slug: string;
  event_title: string;
  as_of_year: number;
  prior_event_count: number;
  projection_mode: string;
  notes: string[];
  characters: UniverseCharacterStateRecord[];
  faction_control: FactionControlStateRecord[];
  artifacts: ArtifactLocationStateRecord[];
};

export type TimelineQuery = {
  startYear?: number;
  endYear?: number;
  era?: string;
  character?: string;
  location?: string;
  causalDepth?: number;
  order?: "asc" | "desc";
  limit?: number;
  offset?: number;
};

export type BackendStatus = "ok" | "degraded" | "offline" | "unknown";

async function getOptionalEntityList<T>(path: string, label: string): Promise<T[]> {
  try {
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      cache: "no-store",
    });

    if (response.ok) {
      return (await response.json()) as T[];
    }

    if (response.status === 404 || response.status === 405) {
      return [];
    }

    throw new Error(`Failed to fetch ${label}: ${response.status}`);
  } catch (error) {
    if (error instanceof Error && error.message.startsWith(`Failed to fetch ${label}:`)) {
      throw error;
    }
    return [];
  }
}

export function formatChronology(year: number): string {
  if (year < 0) {
    return `${Math.abs(year)} BBY`;
  }
  if (year > 0) {
    return `${year} ABY`;
  }
  return "0 ABY";
}

export function formatEventRange(startYear: number, endYear: number | null): string {
  if (endYear === null || endYear === startYear) {
    return formatChronology(startYear);
  }
  return `${formatChronology(startYear)} to ${formatChronology(endYear)}`;
}

export function parseChronologyInput(value: string | string[] | undefined): number | undefined {
  if (typeof value !== "string") {
    return undefined;
  }

  const normalized = value.trim().toUpperCase();
  if (!normalized) {
    return undefined;
  }

  const taggedMatch = normalized.match(/^(-?\d+(?:\.\d+)?)\s*(BBY|ABY)$/);
  if (taggedMatch) {
    const [, rawMagnitude, era] = taggedMatch;
    const magnitude = Number.parseFloat(rawMagnitude);
    if (Number.isNaN(magnitude)) {
      return undefined;
    }
    const absoluteMagnitude = Math.abs(magnitude);
    return era === "BBY" ? -absoluteMagnitude : absoluteMagnitude;
  }

  const numericValue = Number.parseFloat(normalized);
  if (Number.isNaN(numericValue)) {
    return undefined;
  }
  return numericValue;
}

export function formatChronologyInput(value: string | string[] | undefined): string {
  if (typeof value === "string" && value.trim() !== "") {
    return value;
  }

  const parsed = parseChronologyInput(value);
  if (parsed === undefined) {
    return "";
  }
  return formatChronology(parsed);
}

export async function getBackendStatus(): Promise<BackendStatus> {
  try {
    const response = await fetch(`${getApiBaseUrl()}/api/v1/health`, {
      cache: "no-store",
    });
    if (!response.ok) {
      return "degraded";
    }
    const payload = (await response.json()) as { status?: string };
    return payload.status === "ok" ? "ok" : "unknown";
  } catch {
    return "offline";
  }
}

export async function getTimelineEvents(query: TimelineQuery = {}): Promise<EventListResponse> {
  const url = new URL(`${getApiBaseUrl()}/api/v1/events`);
  if (query.startYear !== undefined) {
    url.searchParams.set("start_year", String(query.startYear));
  }
  if (query.endYear !== undefined) {
    url.searchParams.set("end_year", String(query.endYear));
  }
  if (query.era !== undefined) {
    url.searchParams.set("era", query.era);
  }
  if (query.character !== undefined) {
    url.searchParams.set("character", query.character);
  }
  if (query.location !== undefined) {
    url.searchParams.set("location", query.location);
  }
  if (query.causalDepth !== undefined) {
    url.searchParams.set("causal_depth", String(query.causalDepth));
  }
  if (query.order !== undefined) {
    url.searchParams.set("order", query.order);
  }
  if (query.limit !== undefined) {
    url.searchParams.set("limit", String(query.limit));
  }
  if (query.offset !== undefined) {
    url.searchParams.set("offset", String(query.offset));
  }

  const response = await fetch(url.toString(), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch events: ${response.status}`);
  }

  return (await response.json()) as EventListResponse;
}

export async function getEventBySlug(slug: string): Promise<EventRecord> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/events/by-slug/${slug}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch event ${slug}: ${response.status}`);
  }

  return (await response.json()) as EventRecord;
}

export async function getEventUniverseState(eventId: string): Promise<UniverseStateResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/events/${eventId}/universe-state`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch universe state for ${eventId}: ${response.status}`);
  }

  return (await response.json()) as UniverseStateResponse;
}

export async function getCharacters(): Promise<CharacterRecord[]> {
  return getOptionalEntityList<CharacterRecord>("/api/v1/characters", "characters");
}

export async function getCharacterBySlug(slug: string): Promise<CharacterRecord> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/characters/by-slug/${slug}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch character ${slug}: ${response.status}`);
  }

  return (await response.json()) as CharacterRecord;
}

export async function getCharacterTimeline(
  characterId: string,
  query: Omit<TimelineQuery, "character"> = {},
): Promise<EventListResponse> {
  const url = new URL(`${getApiBaseUrl()}/api/v1/characters/${characterId}/timeline`);
  if (query.startYear !== undefined) {
    url.searchParams.set("start_year", String(query.startYear));
  }
  if (query.endYear !== undefined) {
    url.searchParams.set("end_year", String(query.endYear));
  }
  if (query.era !== undefined) {
    url.searchParams.set("era", query.era);
  }
  if (query.location !== undefined) {
    url.searchParams.set("location", query.location);
  }
  if (query.causalDepth !== undefined) {
    url.searchParams.set("causal_depth", String(query.causalDepth));
  }
  if (query.order !== undefined) {
    url.searchParams.set("order", query.order);
  }
  if (query.limit !== undefined) {
    url.searchParams.set("limit", String(query.limit));
  }
  if (query.offset !== undefined) {
    url.searchParams.set("offset", String(query.offset));
  }

  const response = await fetch(url.toString(), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch timeline for character ${characterId}: ${response.status}`);
  }

  return (await response.json()) as EventListResponse;
}

export async function getPlanets(): Promise<PlanetRecord[]> {
  return getOptionalEntityList<PlanetRecord>("/api/v1/planets", "planets");
}

export async function getPlanetBySlug(slug: string): Promise<PlanetRecord> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/planets/by-slug/${slug}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch planet ${slug}: ${response.status}`);
  }

  return (await response.json()) as PlanetRecord;
}

export async function getFactions(): Promise<FactionRecord[]> {
  return getOptionalEntityList<FactionRecord>("/api/v1/factions", "factions");
}

export async function getFactionDetailBySlug(slug: string): Promise<FactionDetailResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/factions/by-slug/${slug}/detail`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch faction detail ${slug}: ${response.status}`);
  }

  return (await response.json()) as FactionDetailResponse;
}

export async function getEventDependencies(
  eventId: string,
  depth?: number,
): Promise<EventRecord[]> {
  const url = new URL(`${getApiBaseUrl()}/api/v1/events/${eventId}/dependencies`);
  if (depth !== undefined) {
    url.searchParams.set("depth", String(depth));
  }

  const response = await fetch(url.toString(), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch dependencies for ${eventId}: ${response.status}`);
  }

  return (await response.json()) as EventRecord[];
}

export async function getEventConsequences(
  eventId: string,
  depth?: number,
): Promise<EventRecord[]> {
  const url = new URL(`${getApiBaseUrl()}/api/v1/events/${eventId}/consequences`);
  if (depth !== undefined) {
    url.searchParams.set("depth", String(depth));
  }

  const response = await fetch(url.toString(), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch consequences for ${eventId}: ${response.status}`);
  }

  return (await response.json()) as EventRecord[];
}

export async function getEventCausalGraph(
  eventId: string,
  depth: number,
): Promise<CausalGraphResponse> {
  const url = new URL(`${getApiBaseUrl()}/api/v1/events/${eventId}/causal-graph`);
  url.searchParams.set("depth", String(depth));

  const response = await fetch(url.toString(), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch causal graph for ${eventId}: ${response.status}`);
  }

  return (await response.json()) as CausalGraphResponse;
}

export async function getEventImpact(eventId: string): Promise<EventImpactResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/events/${eventId}/impact`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch impact for ${eventId}: ${response.status}`);
  }

  return (await response.json()) as EventImpactResponse;
}

export async function simulateTimelineBreak(
  eventId: string,
): Promise<TimelineBreakSimulationResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/engine/simulate-break/${eventId}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to simulate break for ${eventId}: ${response.status}`);
  }

  return (await response.json()) as TimelineBreakSimulationResponse;
}
