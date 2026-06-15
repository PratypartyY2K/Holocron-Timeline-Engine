"use client";

import type { Route } from "next";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState, type FormEvent } from "react";
import {
  type CharacterRecord,
  type FactionRecord,
  formatChronologyInput,
  type PlanetRecord,
  formatChronology,
  formatEventRange,
  getBackendStatus,
  getCharacters,
  getFactions,
  getPlanets,
  getTimelineEvents,
  parseChronologyInput,
  type BackendStatus,
  type EventListResponse,
} from "../lib/holocron-api";
import { searchEntities, type SearchResultRecord } from "../lib/search-api";
import { useAsyncData } from "../lib/use-async-data";
import { ErrorPageFeedback, LoadingPageFeedback } from "./page-feedback";

type HomePageClientProps = {
  initialSearchParams: Record<string, string | string[] | undefined>;
};

type HomePageData = {
  backendStatus: BackendStatus;
  characters: CharacterRecord[];
  factions: FactionRecord[];
  planets: PlanetRecord[];
  searchResults: SearchResultRecord[];
  timeline: EventListResponse;
};

type TimelineZoomLevel = "year" | "decade";
type TimelineGroup = {
  events: EventListResponse["items"];
  id: string;
  label: string;
  summary: string;
};

function buildEraSummary(eras: Array<string | null>): string {
  const eraSet = new Set(eras.filter((era): era is string => Boolean(era)));
  return `${eraSet.size} eras mapped`;
}

function parseOrder(value: string | string[] | undefined): "asc" | "desc" {
  return value === "desc" ? "desc" : "asc";
}

function parseText(value: string | string[] | undefined): string | undefined {
  if (typeof value !== "string" || value.trim() === "") {
    return undefined;
  }
  return value;
}

function entityMetaLabel(entity: CharacterRecord | PlanetRecord | FactionRecord): string {
  if ("species" in entity) {
    return entity.species ?? entity.homeworld_name ?? "Character profile";
  }
  if ("region" in entity) {
    return entity.region ?? "Planet record";
  }
  return "Faction record";
}

function searchResultHref(result: SearchResultRecord): Route {
  if (result.entity_type === "event") {
    return `/events/${result.slug}` as Route;
  }
  if (result.entity_type === "character") {
    return `/characters/${result.slug}` as Route;
  }
  if (result.entity_type === "planet") {
    return `/planets/${result.slug}` as Route;
  }
  return `/factions/${result.slug}` as Route;
}

function searchSectionTitle(query: string, total: number): string {
  if (total === 0) {
    return `No matches for "${query}"`;
  }
  return `${total} match${total === 1 ? "" : "es"} for "${query}"`;
}

function decadeStart(year: number): number {
  return Math.floor(year / 10) * 10;
}

function decadeLabel(year: number): string {
  const start = decadeStart(year);
  const end = start + 9;
  return `${formatChronology(start)} to ${formatChronology(end)}`;
}

function buildTimelineGroups(
  items: EventListResponse["items"],
  zoomLevel: TimelineZoomLevel,
): TimelineGroup[] {
  const groups = new Map<string, TimelineGroup>();

  for (const event of items) {
    const key = zoomLevel === "year" ? String(event.start_year) : `decade:${decadeStart(event.start_year)}`;
    const label = zoomLevel === "year" ? formatChronology(event.start_year) : decadeLabel(event.start_year);
    const summary = zoomLevel === "year" ? "Year view" : "Decade view";
    const current = groups.get(key) ?? {
      events: [],
      id: key,
      label,
      summary,
    };
    current.events.push(event);
    groups.set(key, current);
  }

  return Array.from(groups.values());
}

function renderSearchResults(query: string, items: SearchResultRecord[]) {
  const groupedResults = new Map<SearchResultRecord["entity_type"], SearchResultRecord[]>();
  for (const item of items) {
    const bucket = groupedResults.get(item.entity_type) ?? [];
    bucket.push(item);
    groupedResults.set(item.entity_type, bucket);
  }

  const orderedGroups: Array<[SearchResultRecord["entity_type"], string]> = [
    ["event", "Events"],
    ["character", "Characters"],
    ["planet", "Planets"],
    ["faction", "Factions"],
  ];

  return (
    <section className="timeline-shell search-shell">
      <header className="timeline-header search-header">
        <div>
          <p className="section-kicker">Search</p>
          <h2>{searchSectionTitle(query, items.length)}</h2>
        </div>
        <p className="timeline-caption">
          Browser-fetched from <code>/api/v1/search?q={query}</code> across events, characters,
          planets, and factions.
        </p>
      </header>
      {items.length === 0 ? (
        <p className="detail-empty">
          Try a character, event title, slug, faction, or world name.
        </p>
      ) : (
        <div className="search-groups">
          {orderedGroups.map(([entityType, label]) => {
            const groupItems = groupedResults.get(entityType) ?? [];
            if (groupItems.length === 0) {
              return null;
            }
            return (
              <section key={entityType} className="search-group">
                <div className="search-group-header">
                  <p className="section-kicker">{label}</p>
                  <span className="search-count">{groupItems.length}</span>
                </div>
                <div className="search-grid">
                  {groupItems.map((item) => (
                    <Link key={`${item.entity_type}-${item.id}`} href={searchResultHref(item)} className="search-card">
                      <div className="search-card-meta">
                        <span>{item.entity_type}</span>
                        <span>/{item.slug}</span>
                      </div>
                      <h3>{item.label}</h3>
                      <p>{item.description ?? "No description available."}</p>
                    </Link>
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      )}
    </section>
  );
}

function renderEntityPreview(
  title: string,
  kicker: string,
  href: Route,
  items: Array<CharacterRecord | PlanetRecord | FactionRecord>,
) {
  return (
    <section className="timeline-shell entity-shell">
      <header className="timeline-header entity-header">
        <div>
          <p className="section-kicker">{kicker}</p>
          <h2>{title}</h2>
        </div>
        <p className="timeline-caption">
          Structured node profiles synced from the graph backend.
        </p>
      </header>
      <div className="entity-grid">
        {items.map((item) => (
          <Link
            key={item.id}
            href={`${href}/${item.slug}` as Route}
            className="entity-card"
          >
            <div className="entity-card-meta">
              <span>{entityMetaLabel(item)}</span>
              <span>/{item.slug}</span>
            </div>
            <h3>{item.name}</h3>
            <p>{item.description ?? "No description available."}</p>
          </Link>
        ))}
      </div>
      <div className="entity-footer">
        <Link href={href} className="secondary-link">
          Browse all
        </Link>
      </div>
    </section>
  );
}

export function HomePageClient({ initialSearchParams }: HomePageClientProps) {
  const router = useRouter();
  const [timelineZoomLevel, setTimelineZoomLevel] = useState<TimelineZoomLevel>("year");
  const startYear = parseChronologyInput(initialSearchParams.start_year);
  const endYear = parseChronologyInput(initialSearchParams.end_year);
  const startYearInput = formatChronologyInput(initialSearchParams.start_year);
  const endYearInput = formatChronologyInput(initialSearchParams.end_year);
  const order = parseOrder(initialSearchParams.order);
  const era = parseText(initialSearchParams.era);
  const character = parseText(initialSearchParams.character);
  const location = parseText(initialSearchParams.location);
  const searchQuery = parseText(initialSearchParams.q);

  function handleTimelineFilterSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const params = new URLSearchParams();
    const startYearValue = formData.get("start_year");
    const endYearValue = formData.get("end_year");
    const orderValue = formData.get("order");
    const eraValue = formData.get("era");
    const characterValue = formData.get("character");
    const locationValue = formData.get("location");
    const queryValue = searchQuery ?? "";

    if (typeof queryValue === "string" && queryValue.trim() !== "") {
      params.set("q", queryValue);
    }
    if (typeof startYearValue === "string" && startYearValue.trim() !== "") {
      params.set("start_year", startYearValue.trim());
    }
    if (typeof endYearValue === "string" && endYearValue.trim() !== "") {
      params.set("end_year", endYearValue.trim());
    }
    if (typeof orderValue === "string" && orderValue.trim() !== "" && orderValue !== "asc") {
      params.set("order", orderValue);
    }
    if (typeof eraValue === "string" && eraValue.trim() !== "") {
      params.set("era", eraValue);
    }
    if (typeof characterValue === "string" && characterValue.trim() !== "") {
      params.set("character", characterValue);
    }
    if (typeof locationValue === "string" && locationValue.trim() !== "") {
      params.set("location", locationValue);
    }

    const query = params.toString();
    router.push((query ? `/?${query}` : "/") as Route);
  }

  const { data, error, isLoading } = useAsyncData<HomePageData>(
    async () => {
      const [backendStatus, timeline, characters, planets, factions, searchResults] = await Promise.all([
        getBackendStatus(),
        getTimelineEvents({
          startYear,
          endYear,
          era,
          character,
          location,
          order,
          limit: 200,
        }),
        getCharacters(),
        getPlanets(),
        getFactions(),
        searchQuery ? searchEntities(searchQuery, 12) : Promise.resolve([]),
      ]);

      return {
        backendStatus,
        characters,
        factions,
        planets,
        searchResults,
        timeline,
      };
    },
    [startYear, endYear, order, era, character, location, searchQuery],
  );

  const knownEras = useMemo(
    () =>
      Array.from(
        new Set(
          (data?.timeline.items ?? [])
            .map((event) => event.era)
            .filter((item): item is string => Boolean(item)),
        ),
      ).sort((left, right) => left.localeCompare(right)),
    [data?.timeline.items],
  );
  const timelineGroups = useMemo(
    () => buildTimelineGroups(data?.timeline.items ?? [], timelineZoomLevel),
    [data?.timeline.items, timelineZoomLevel],
  );

  if (isLoading) {
    return (
      <LoadingPageFeedback
        title="Archive overview"
        message="Loading timeline and entity data from the browser."
      />
    );
  }

  if (error || !data) {
    return (
      <ErrorPageFeedback
        title="Archive overview"
        message={error ?? "Timeline data could not be loaded."}
      />
    );
  }

  const firstEvent = data.timeline.items.at(0);
  const lastEvent = data.timeline.items.at(-1);
  const rangeLabel =
    firstEvent && lastEvent
      ? `${formatChronology(firstEvent.start_year)} to ${formatChronology(lastEvent.start_year)}`
      : "No events available";

  return (
    <main className="page-shell">
      <section className="hero hero-wide">
        <div className="hero-copy">
          <p className="eyebrow">Holocron Timeline Engine</p>
          <h1>Galaxy history, characters, worlds, and factions in one archive.</h1>
          <p className="lede">
            A timeline-first Star Wars explorer with event chronology, graph-aware filters,
            and browsable entity records for the major actors in the canon.
          </p>
          <form className="search-bar" method="get">
            <label className="search-field">
              <span className="search-label">Archive search</span>
              <input
                type="search"
                name="q"
                defaultValue={searchQuery ?? ""}
                placeholder="Search for Anakin, Order 66, Coruscant..."
              />
            </label>
            <button type="submit" className="action-button">
              Search archive
            </button>
            {searchQuery ? (
              <Link href={"/" as Route} className="secondary-link">
                Clear search
              </Link>
            ) : null}
          </form>
          <nav className="hero-nav" aria-label="Primary">
            <Link href={"/events" as Route} className="secondary-link">
              Events
            </Link>
            <Link href={"/characters" as Route} className="secondary-link">
              Characters
            </Link>
            <Link href={"/planets" as Route} className="secondary-link">
              Planets
            </Link>
            <Link href={"/factions" as Route} className="secondary-link">
              Factions
            </Link>
          </nav>
        </div>

        <div className="hero-stats">
          <div className="stat-card">
            <span className="stat-label">Backend</span>
            <span className={`status-pill status-${data.backendStatus}`}>{data.backendStatus}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Event range</span>
            <strong>{rangeLabel}</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Entity coverage</span>
            <strong>{data.characters.length + data.planets.length + data.factions.length} graph nodes</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Coverage</span>
            <strong>{buildEraSummary(data.timeline.items.map((event) => event.era))}</strong>
          </div>
        </div>
      </section>

      {searchQuery ? renderSearchResults(searchQuery, data.searchResults) : null}

      <section className="timeline-shell">
        <header className="timeline-header">
          <div>
            <p className="section-kicker">Chronology</p>
            <h2>Mapped events</h2>
          </div>
          <p className="timeline-caption">
            Browser-fetched from <code>/api/v1/events</code>. Filters now span time, era,
            character involvement, and location.
          </p>
        </header>

        <div className="timeline-zoom-bar" role="tablist" aria-label="Timeline zoom">
          <button
            type="button"
            className={`timeline-zoom-button${timelineZoomLevel === "year" ? " is-active" : ""}`}
            onClick={() => setTimelineZoomLevel("year")}
          >
            Year view
          </button>
          <button
            type="button"
            className={`timeline-zoom-button${timelineZoomLevel === "decade" ? " is-active" : ""}`}
            onClick={() => setTimelineZoomLevel("decade")}
          >
            Decade view
          </button>
        </div>

        <form
          className="filter-bar filter-bar-wide"
          method="get"
          onSubmit={handleTimelineFilterSubmit}
        >
          <label className="filter-field">
            <span>Start chronology</span>
            <input
              type="text"
              name="start_year"
              defaultValue={startYearInput}
              placeholder="32 BBY"
            />
          </label>
          <label className="filter-field">
            <span>End chronology</span>
            <input
              type="text"
              name="end_year"
              defaultValue={endYearInput}
              placeholder="4 ABY"
            />
          </label>
          <label className="filter-field">
            <span>Order</span>
            <select name="order" defaultValue={order}>
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>
          </label>
          <label className="filter-field">
            <span>Era</span>
            <select name="era" defaultValue={era ?? ""}>
              <option value="">All eras</option>
              {knownEras.map((knownEra) => (
                <option key={knownEra} value={knownEra}>
                  {knownEra}
                </option>
              ))}
            </select>
          </label>
          <label className="filter-field">
            <span>Character</span>
            <select name="character" defaultValue={character ?? ""}>
              <option value="">Any character</option>
              {data.characters.map((item) => (
                <option key={item.id} value={item.slug}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <label className="filter-field">
            <span>Location</span>
            <select name="location" defaultValue={location ?? ""}>
              <option value="">Any planet</option>
              {data.planets.map((item) => (
                <option key={item.id} value={item.slug}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <div className="filter-actions">
            <button type="submit" className="action-button">
              Apply filters
            </button>
            <Link href={"/" as Route} className="secondary-link">
              Reset
            </Link>
          </div>
        </form>

        <div className="timeline-groups">
          {timelineGroups.map((group) => (
            <section key={group.id} className="timeline-group">
              <header className="timeline-group-header">
                <div>
                  <p className="section-kicker">{group.summary}</p>
                  <h3>{group.label}</h3>
                </div>
                <span className="timeline-group-count">{group.events.length} events</span>
              </header>
              <div className="timeline-list">
                {group.events.map((event) => (
                  <article key={event.id} className="timeline-card">
                    <div className="timeline-marker" aria-hidden="true" />
                    <Link
                      href={`/events/${event.slug}` as Route}
                      className="timeline-card-body timeline-link-card"
                    >
                      <div className="timeline-meta">
                        <span className="timeline-year">{formatEventRange(event.start_year, event.end_year)}</span>
                        <span className="timeline-era">{event.era ?? "Unclassified era"}</span>
                      </div>
                      <h3>{event.title}</h3>
                      <p>{event.description ?? "No description available."}</p>
                    </Link>
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      </section>

      {renderEntityPreview("Character archive", "Personae", "/characters", data.characters.slice(0, 6))}
      {renderEntityPreview("Planetary atlas", "Atlas", "/planets", data.planets.slice(0, 6))}
      {renderEntityPreview("Faction registry", "Power blocs", "/factions", data.factions.slice(0, 6))}
    </main>
  );
}
