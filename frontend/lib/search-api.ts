export type SearchResultRecord = {
  entity_type: "event" | "character" | "planet" | "faction";
  id: string;
  slug: string;
  label: string;
  description: string | null;
};

const DEFAULT_BROWSER_API_BASE_URL = "http://localhost:8000";
const DEFAULT_SERVER_API_BASE_URL = "http://backend:8000";

function resolveBrowserApiBaseUrl(configuredApiBaseUrl: string | undefined): string {
  if (!configuredApiBaseUrl) {
    return DEFAULT_BROWSER_API_BASE_URL;
  }

  try {
    const url = new URL(configuredApiBaseUrl);
    if (url.hostname === "backend") {
      url.hostname = "localhost";
    }
    return url.toString().replace(/\/$/, "");
  } catch {
    return configuredApiBaseUrl;
  }
}

function getApiBaseUrl(): string {
  const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (typeof window === "undefined") {
    return configuredApiBaseUrl ?? DEFAULT_SERVER_API_BASE_URL;
  }
  return resolveBrowserApiBaseUrl(configuredApiBaseUrl);
}

export async function searchEntities(query: string, limit = 12): Promise<SearchResultRecord[]> {
  const url = new URL(`${getApiBaseUrl()}/api/v1/search`);
  url.searchParams.set("q", query);
  url.searchParams.set("limit", String(limit));

  const response = await fetch(url.toString(), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to search for ${query}: ${response.status}`);
  }

  return (await response.json()) as SearchResultRecord[];
}
