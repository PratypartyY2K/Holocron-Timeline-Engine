export type SearchResultRecord = {
  entity_type: "event" | "character" | "planet" | "faction";
  id: string;
  slug: string;
  label: string;
  description: string | null;
};

import { getApiBaseUrl } from "./api-base-url";

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
