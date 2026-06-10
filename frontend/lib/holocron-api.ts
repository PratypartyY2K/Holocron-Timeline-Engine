export type EventRecord = {
  id: string;
  slug: string;
  title: string;
  description: string | null;
  start_year: number;
  end_year: number | null;
  era: string | null;
  canon_status: string | null;
  source_refs: string[];
  created_at: string;
  updated_at: string;
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

const DEFAULT_API_BASE_URL = "http://backend:8000";

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
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
