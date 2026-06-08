import type { Route } from "next";
import Link from "next/link";
import {
  formatChronology,
  formatEventRange,
  EventRecord,
  getBackendStatus,
  getTimelineEvents,
} from "../lib/holocron-api";

function buildEraSummary(events: Awaited<ReturnType<typeof getTimelineEvents>>["items"]): string {
  const eraSet = new Set(events.map((event) => event.era).filter((era): era is string => Boolean(era)));
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

function parseEra(value: string | string[] | undefined): string | undefined {
  if (typeof value !== "string" || value.trim() === "") {
    return undefined;
  }
  return value;
}

function filterByEra(events: EventRecord[], era: string | undefined): EventRecord[] {
  if (era === undefined) {
    return events;
  }
  return events.filter((event) => event.era === era);
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const startYear = parseInteger(resolvedSearchParams.start_year);
  const endYear = parseInteger(resolvedSearchParams.end_year);
  const order = parseOrder(resolvedSearchParams.order);
  const era = parseEra(resolvedSearchParams.era);

  const [backendStatus, timeline] = await Promise.all([
    getBackendStatus(),
    getTimelineEvents({
      startYear,
      endYear,
      order,
      limit: 200,
    }),
  ]);
  const filteredItems = filterByEra(timeline.items, era);
  const knownEras = Array.from(
    new Set(timeline.items.map((event) => event.era).filter((item): item is string => Boolean(item))),
  ).sort((left, right) => left.localeCompare(right));
  const firstEvent = filteredItems.at(0);
  const lastEvent = filteredItems.at(-1);
  const rangeLabel =
    firstEvent && lastEvent
      ? `${formatChronology(firstEvent.start_year)} to ${formatChronology(lastEvent.start_year)}`
      : "No events available";

  return (
    <main className="page-shell">
      <section className="hero hero-wide">
        <div className="hero-copy">
          <p className="eyebrow">Holocron Timeline Engine</p>
          <h1>Galaxy history, arranged as a living chronology.</h1>
          <p className="lede">
            A timeline-first view of Star Wars canon, backed by FastAPI and Neo4j and ready
            for graph exploration.
          </p>
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
            <span className="stat-label">Archive size</span>
            <strong>{filteredItems.length} events</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Coverage</span>
            <strong>{buildEraSummary(filteredItems)}</strong>
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
            Server-rendered from <code>/api/v1/events</code>. Signed backend chronology is
            formatted here as BBY and ABY.
          </p>
        </header>

        <form className="filter-bar" method="get">
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
          <div className="filter-actions">
            <button type="submit" className="action-button">
              Apply filters
            </button>
            <Link href={"/events" as Route} className="secondary-link">
              Reset
            </Link>
          </div>
        </form>

        <div className="timeline-list">
          {filteredItems.map((event) => (
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
    </main>
  );
}
