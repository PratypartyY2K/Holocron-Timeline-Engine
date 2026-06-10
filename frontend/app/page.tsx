import type { Route } from "next";
import Link from "next/link";
import {
  CharacterRecord,
  FactionRecord,
  PlanetRecord,
  formatChronology,
  formatEventRange,
  getBackendStatus,
  getCharacters,
  getFactions,
  getPlanets,
  getTimelineEvents,
} from "../lib/holocron-api";

function buildEraSummary(eras: Array<string | null>): string {
  const eraSet = new Set(eras.filter((era): era is string => Boolean(era)));
  return `${eraSet.size} eras mapped`;
}

type HomePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function parseInteger(value: string | string[] | undefined): number | undefined {
  if (typeof value !== "string" || value.trim() === "") {
    return undefined;
  }
  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) ? undefined : parsed;
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

export default async function HomePage({ searchParams }: HomePageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const startYear = parseInteger(resolvedSearchParams.start_year);
  const endYear = parseInteger(resolvedSearchParams.end_year);
  const order = parseOrder(resolvedSearchParams.order);
  const era = parseText(resolvedSearchParams.era);
  const character = parseText(resolvedSearchParams.character);
  const location = parseText(resolvedSearchParams.location);

  const [backendStatus, timeline, characters, planets, factions] = await Promise.all([
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
  ]);

  const knownEras = Array.from(
    new Set(timeline.items.map((event) => event.era).filter((item): item is string => Boolean(item))),
  ).sort((left, right) => left.localeCompare(right));
  const firstEvent = timeline.items.at(0);
  const lastEvent = timeline.items.at(-1);
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
            <span className={`status-pill status-${backendStatus}`}>{backendStatus}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Event range</span>
            <strong>{rangeLabel}</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Entity coverage</span>
            <strong>{characters.length + planets.length + factions.length} graph nodes</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Coverage</span>
            <strong>{buildEraSummary(timeline.items.map((event) => event.era))}</strong>
          </div>
        </div>
      </section>

      <section className="timeline-shell">
        <header className="timeline-header">
          <div>
            <p className="section-kicker">Chronology</p>
            <h2>Mapped events</h2>
          </div>
          <p className="timeline-caption">
            Server-rendered from <code>/api/v1/events</code>. Filters now span time, era,
            character involvement, and location.
          </p>
        </header>

        <form className="filter-bar filter-bar-wide" method="get">
          <label className="filter-field">
            <span>Start year</span>
            <input type="number" name="start_year" defaultValue={startYear} placeholder="-232" />
          </label>
          <label className="filter-field">
            <span>End year</span>
            <input type="number" name="end_year" defaultValue={endYear} placeholder="35" />
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
              {characters.map((item) => (
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
              {planets.map((item) => (
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

        <div className="timeline-list">
          {timeline.items.map((event) => (
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
                <div className="timeline-footer">
                  <span className="timeline-slug">/{event.slug}</span>
                  <span className="timeline-source">
                    {event.source_refs.length > 0 ? event.source_refs.join(" • ") : "No sources"}
                  </span>
                </div>
              </Link>
            </article>
          ))}
        </div>
      </section>

      {renderEntityPreview("Key characters", "Personae", "/characters", characters.slice(0, 3))}
      {renderEntityPreview("Known worlds", "Atlas", "/planets", planets.slice(0, 3))}
      {renderEntityPreview("Power blocs", "Factions", "/factions", factions.slice(0, 3))}
    </main>
  );
}
