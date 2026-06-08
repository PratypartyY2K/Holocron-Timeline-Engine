import type { Route } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { EventFocusGraph } from "../../../components/event-focus-graph";
import {
  EventRecord,
  formatEventRange,
  getEventBySlug,
  getEventCausalGraph,
  getEventConsequences,
  getEventDependencies,
} from "../../../lib/holocron-api";

type EventDetailPageProps = {
  params: Promise<{
    slug: string;
  }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function parseDepth(value: string | string[] | undefined): number {
  if (typeof value !== "string" || value.trim() === "") {
    return 2;
  }
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed) || parsed < 1) {
    return 2;
  }
  return parsed;
}

function renderEventList(items: EventRecord[], emptyLabel: string) {
  if (items.length === 0) {
    return <p className="detail-empty">{emptyLabel}</p>;
  }

  return (
    <div className="detail-list">
      {items.map((event) => (
        <Link
          key={event.id}
          href={`/events/${event.slug}` as Route}
          className="detail-list-card"
        >
          <div className="detail-list-meta">
            <span>{formatEventRange(event.start_year, event.end_year)}</span>
            <span>{event.era ?? "Unclassified era"}</span>
          </div>
          <h3>{event.title}</h3>
          <p>{event.description ?? "No description available."}</p>
        </Link>
      ))}
    </div>
  );
}

export default async function EventDetailPage({ params, searchParams }: EventDetailPageProps) {
  const { slug } = await params;
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const depth = parseDepth(resolvedSearchParams.depth);

  let event: EventRecord;
  try {
    event = await getEventBySlug(slug);
  } catch {
    notFound();
  }

  const [dependencies, consequences, causalGraph] = await Promise.all([
    getEventDependencies(event.id, depth),
    getEventConsequences(event.id, depth),
    getEventCausalGraph(event.id, depth),
  ]);

  return (
    <main className="page-shell">
      <section className="hero detail-hero">
        <div className="detail-breadcrumb-row">
          <Link href={"/events" as Route} className="back-link">
            ← Back to timeline
          </Link>
          <span className="detail-chip">{event.era ?? "Unclassified era"}</span>
        </div>

        <div className="detail-meta">
          <span className="timeline-year">{formatEventRange(event.start_year, event.end_year)}</span>
          <span className="detail-slug">/{event.slug}</span>
        </div>

        <h1>{event.title}</h1>
        <p className="detail-description">{event.description ?? "No description available."}</p>

        <div className="hero-stats detail-stats">
          <div className="stat-card">
            <span className="stat-label">Canon status</span>
            <strong>{event.canon_status ?? "Unspecified"}</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Sources</span>
            <strong>{event.source_refs.length > 0 ? event.source_refs.join(", ") : "No sources"}</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Dependencies</span>
            <strong>{dependencies.length} within depth {depth}</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Consequences</span>
            <strong>{consequences.length} within depth {depth}</strong>
          </div>
        </div>
      </section>

      <section className="timeline-shell graph-panel">
        <EventFocusGraph graph={causalGraph} />
      </section>

      <section className="detail-grid">
        <section className="timeline-shell detail-panel">
          <header className="timeline-header detail-panel-header">
            <div>
              <p className="section-kicker">Dependencies</p>
              <h2>Events that lead here</h2>
            </div>
            <p className="timeline-caption">
              Showing causal ancestors from <code>/dependencies?depth={depth}</code>.
            </p>
          </header>
          <form className="detail-toolbar" method="get">
            <label className="filter-field">
              <span>Traversal depth</span>
              <select name="depth" defaultValue={String(depth)}>
                <option value="1">1 hop</option>
                <option value="2">2 hops</option>
                <option value="3">3 hops</option>
                <option value="4">4 hops</option>
                <option value="5">5 hops</option>
              </select>
            </label>
            <div className="filter-actions">
              <button type="submit" className="action-button">
                Apply depth
              </button>
            </div>
          </form>
          {renderEventList(dependencies, `No upstream dependencies found within depth ${depth}.`)}
        </section>

        <section className="timeline-shell detail-panel">
          <header className="timeline-header detail-panel-header">
            <div>
              <p className="section-kicker">Consequences</p>
              <h2>Events that follow from this</h2>
            </div>
            <p className="timeline-caption">
              Showing downstream effects from <code>/consequences?depth={depth}</code>.
            </p>
          </header>
          {renderEventList(consequences, `No downstream consequences found within depth ${depth}.`)}
        </section>
      </section>
    </main>
  );
}
