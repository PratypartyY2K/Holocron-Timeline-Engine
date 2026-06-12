"use client";

import type { Route } from "next";
import Link from "next/link";
import { useState } from "react";
import { EventFocusGraph } from "./event-focus-graph";
import {
  type EventRecord,
  formatEventRange,
  getEventBySlug,
  getEventCausalGraph,
  getEventConsequences,
  getEventDependencies,
  getEventImpact,
  type CausalGraphResponse,
  type EventImpactResponse,
} from "../lib/holocron-api";
import { useAsyncData } from "../lib/use-async-data";
import { ErrorPageFeedback, LoadingPageFeedback } from "./page-feedback";

type EventDetailPageClientProps = {
  depth: number;
  slug: string;
};

type EventDetailData = {
  causalGraph: CausalGraphResponse;
  consequences: EventRecord[];
  dependencies: EventRecord[];
  event: EventRecord;
};

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

export function EventDetailPageClient({ depth, slug }: EventDetailPageClientProps) {
  const [isWhatIfEnabled, setIsWhatIfEnabled] = useState(false);
  const { data, error, isLoading } = useAsyncData<EventDetailData>(
    async () => {
      const event = await getEventBySlug(slug);
      const [dependencies, consequences, causalGraph] = await Promise.all([
        getEventDependencies(event.id, depth),
        getEventConsequences(event.id, depth),
        getEventCausalGraph(event.id, depth),
      ]);

      return {
        causalGraph,
        consequences,
        dependencies,
        event,
      };
    },
    [depth, slug],
  );
  const impactEventId = isWhatIfEnabled ? data?.event.id ?? null : null;
  const {
    data: impactData,
    error: impactError,
    isLoading: isImpactLoading,
  } = useAsyncData<EventImpactResponse | null>(
    async () => {
      if (!impactEventId) {
        return null;
      }
      return getEventImpact(impactEventId);
    },
    [impactEventId],
  );

  if (isLoading) {
    return (
      <LoadingPageFeedback
        title="Event detail"
        message="Loading event detail and graph data from the browser."
      />
    );
  }

  if (error || !data) {
    return (
      <ErrorPageFeedback
        title="Event detail"
        message={error ?? "Event data could not be loaded."}
      />
    );
  }

  return (
    <main className="page-shell">
      <section className="hero detail-hero">
        <div className="detail-breadcrumb-row">
          <Link href={"/events" as Route} className="back-link">
            ← Back to timeline
          </Link>
          <span className="detail-chip">{data.event.era ?? "Unclassified era"}</span>
        </div>

        <div className="detail-meta">
          <span className="timeline-year">{formatEventRange(data.event.start_year, data.event.end_year)}</span>
          <span className="detail-slug">/{data.event.slug}</span>
        </div>

        <h1>{data.event.title}</h1>
        <p className="detail-description">{data.event.description ?? "No description available."}</p>

        <div className="hero-stats detail-stats">
          <div className="stat-card">
            <span className="stat-label">Canon status</span>
            <strong>{data.event.canon_status ?? "Unspecified"}</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Sources</span>
            <strong>{data.event.source_refs.length > 0 ? data.event.source_refs.join(", ") : "No sources"}</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Dependencies</span>
            <strong>{data.dependencies.length} within depth {depth}</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Consequences</span>
            <strong>{data.consequences.length} within depth {depth}</strong>
          </div>
        </div>
      </section>

      <section className="timeline-shell graph-panel">
        <div className="sandbox-toolbar">
          <div>
            <p className="section-kicker">Sandbox</p>
            <h2>What-if simulation</h2>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={isWhatIfEnabled}
            className={`what-if-toggle${isWhatIfEnabled ? " is-enabled" : ""}`}
            onClick={() => setIsWhatIfEnabled((current) => !current)}
          >
            <span className="what-if-toggle-track">
              <span className="what-if-toggle-thumb" />
            </span>
            <span className="what-if-toggle-copy">
              {isWhatIfEnabled ? "What-if active" : "What-if off"}
            </span>
          </button>
        </div>

        <p className="timeline-caption sandbox-caption">
          {isWhatIfEnabled
            ? isImpactLoading
              ? "Calculating which downstream events and links would fail if this event were altered."
              : impactError
                ? impactError
                : `Altering this event would break ${impactData?.impacted_events.length ?? 0} downstream events across ${impactData?.broken_edges.length ?? 0} causal links.`
            : "Toggle the sandbox to simulate removing this event from the timeline and inspect the broken downstream path."}
        </p>

        <EventFocusGraph
          graph={data.causalGraph}
          impact={impactData}
          impactLoading={isImpactLoading}
          simulateDisabled={isWhatIfEnabled}
        />
      </section>

      <section className="detail-grid">
        <section className="timeline-shell detail-panel">
          <header className="timeline-header detail-panel-header">
            <div>
              <p className="section-kicker">Dependencies</p>
              <h2>Events that lead here</h2>
            </div>
            <p className="timeline-caption">
              Showing browser-fetched causal ancestors from <code>/dependencies?depth={depth}</code>.
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
          {renderEventList(data.dependencies, `No upstream dependencies found within depth ${depth}.`)}
        </section>

        <section className="timeline-shell detail-panel">
          <header className="timeline-header detail-panel-header">
            <div>
              <p className="section-kicker">Consequences</p>
              <h2>Events that follow from this</h2>
            </div>
            <p className="timeline-caption">
              Showing browser-fetched downstream effects from <code>/consequences?depth={depth}</code>.
            </p>
          </header>
          {renderEventList(data.consequences, `No downstream consequences found within depth ${depth}.`)}
        </section>
      </section>
    </main>
  );
}
