"use client";

import type { Route } from "next";
import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { ArchiveSearchNav } from "./archive-search-nav";
import { EventFocusGraph } from "./event-focus-graph";
import {
  type EventRecord,
  type UniverseStateResponse,
  formatEventRange,
  getEventBySlug,
  getEventCausalGraph,
  getEventConsequences,
  getEventDependencies,
  getEventUniverseState,
  type CausalGraphResponse,
  simulateTimelineBreak,
  type TimelineBreakSimulationResponse,
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
  universeState: UniverseStateResponse;
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

function inlineEntityLink(href: Route, label: string) {
  return (
    <Link href={href} className="inline-entity-link">
      {label}
    </Link>
  );
}

export function EventDetailPageClient({ depth, slug }: EventDetailPageClientProps) {
  const [isWhatIfEnabled, setIsWhatIfEnabled] = useState(false);
  const [dependencyDepth, setDependencyDepth] = useState(depth);
  const [dependencyDepthDraft, setDependencyDepthDraft] = useState(String(depth));
  const [consequenceDepth, setConsequenceDepth] = useState(depth);
  const [consequenceDepthDraft, setConsequenceDepthDraft] = useState(String(depth));
  const { data, error, isLoading } = useAsyncData<EventDetailData>(
    async () => {
      const event = await getEventBySlug(slug);
      const [dependencies, consequences, causalGraph] = await Promise.all([
        getEventDependencies(event.id, depth),
        getEventConsequences(event.id, depth),
        getEventCausalGraph(event.id, depth),
      ]);
      const universeState = await getEventUniverseState(event.id);

      return {
        causalGraph,
        consequences,
        dependencies,
        event,
        universeState,
      };
    },
    [depth, slug],
  );
  const {
    data: dependencyItems,
    error: dependencyError,
    isLoading: isDependencyLoading,
  } = useAsyncData<EventRecord[] | null>(
    async () => {
      if (!data?.event.id) {
        return null;
      }
      return getEventDependencies(data.event.id, dependencyDepth);
    },
    [data?.event.id, dependencyDepth],
  );
  const {
    data: consequenceItems,
    error: consequenceError,
    isLoading: isConsequenceLoading,
  } = useAsyncData<EventRecord[] | null>(
    async () => {
      if (!data?.event.id) {
        return null;
      }
      return getEventConsequences(data.event.id, consequenceDepth);
    },
    [consequenceDepth, data?.event.id],
  );
  const impactEventId = isWhatIfEnabled ? data?.event.id ?? null : null;
  const {
    data: simulationData,
    error: simulationError,
    isLoading: isSimulationLoading,
  } = useAsyncData<TimelineBreakSimulationResponse | null>(
    async () => {
      if (!impactEventId) {
        return null;
      }
      return simulateTimelineBreak(impactEventId);
    },
    [impactEventId],
  );

  const invalidatedCount =
    simulationData?.nodes.filter((node) => node.status === "invalidated").length ?? 0;
  const unresolvedCount =
    simulationData?.nodes.filter((node) => node.status === "unresolved").length ?? 0;

  const eventImportance = data?.event.centrality_score.toFixed(2) ?? "0.00";

  useEffect(() => {
    setDependencyDepth(depth);
    setDependencyDepthDraft(String(depth));
    setConsequenceDepth(depth);
    setConsequenceDepthDraft(String(depth));
  }, [depth, slug]);

  function handleDependencyDepthSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const nextDepth = Number.parseInt(dependencyDepthDraft, 10);
    if (!Number.isNaN(nextDepth) && nextDepth >= 1 && nextDepth <= 5) {
      setDependencyDepth(nextDepth);
    }
  }

  function handleConsequenceDepthSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const nextDepth = Number.parseInt(consequenceDepthDraft, 10);
    if (!Number.isNaN(nextDepth) && nextDepth >= 1 && nextDepth <= 5) {
      setConsequenceDepth(nextDepth);
    }
  }

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
        <ArchiveSearchNav />

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
            <span className="stat-label">Dependency weight</span>
            <strong>{data.event.dependency_count} total upstream events</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Importance</span>
            <strong>{eventImportance} centrality</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Visible dependencies</span>
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
            <p className="sandbox-scenario">
              What if <strong>{data.event.title}</strong> never happened?
            </p>
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
            ? isSimulationLoading
              ? `Calculating how the timeline changes if ${data.event.title} is removed from history.`
              : simulationError
                ? simulationError
                : `If ${data.event.title} never happened, the alternate branch marks ${invalidatedCount} events invalidated and ${unresolvedCount} unresolved across ${simulationData?.edges.length ?? 0} causal links.`
            : `Toggle the sandbox to explore what breaks if ${data.event.title} never occurs.`}
        </p>

        <EventFocusGraph
          graph={data.causalGraph}
          simulation={simulationData}
          simulationLoading={isSimulationLoading}
          simulateEnabled={isWhatIfEnabled}
        />
      </section>

      <section className="detail-grid">
        <section className="timeline-shell detail-panel detail-panel-full">
          <header className="timeline-header detail-panel-header">
            <div>
              <p className="section-kicker">Universe State</p>
              <h2>Tracked snapshot before this event</h2>
            </div>
            <p className="timeline-caption">
              The backend projects tracked characters, planetary control, and artifact positions before
              <code> /events/{data.event.slug}</code> begins.
            </p>
          </header>

          <div className="universe-state-grid">
            <section className="universe-state-card">
              <h3>Tracked characters</h3>
              <div className="universe-state-list">
                {data.universeState.characters.map((character) => (
                  <article key={character.id} className="universe-state-row">
                    <div>
                      <strong>
                        {inlineEntityLink(`/characters/${character.slug}` as Route, character.name)}
                      </strong>
                      <p>
                        {character.is_alive ? "Alive" : "Dead"}
                        {character.location_planet_name && character.location_planet_slug ? (
                          <>
                            {" · "}
                            {inlineEntityLink(
                              `/planets/${character.location_planet_slug}` as Route,
                              character.location_planet_name,
                            )}
                          </>
                        ) : null}
                      </p>
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className="universe-state-card">
              <h3>Planetary control</h3>
              <div className="universe-state-list">
                {data.universeState.faction_control.map((control) => (
                  <article key={control.planet_slug} className="universe-state-row">
                    <div>
                      <strong>
                        {inlineEntityLink(`/planets/${control.planet_slug}` as Route, control.planet_name)}
                      </strong>
                      <p>{inlineEntityLink(`/factions/${control.faction_slug}` as Route, control.faction_name)}</p>
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className="universe-state-card">
              <h3>Tracked artifacts</h3>
              <div className="universe-state-list">
                {data.universeState.artifacts.map((artifact) => (
                  <article key={artifact.artifact_key} className="universe-state-row">
                    <div>
                      <strong>{artifact.artifact_name}</strong>
                      <p>
                        {artifact.holder_character_name && artifact.holder_character_slug
                          ? inlineEntityLink(
                              `/characters/${artifact.holder_character_slug}` as Route,
                              artifact.holder_character_name,
                            )
                          : "Unknown holder"}
                        {artifact.location_planet_name && artifact.location_planet_slug ? (
                          <>
                            {" · "}
                            {inlineEntityLink(
                              `/planets/${artifact.location_planet_slug}` as Route,
                              artifact.location_planet_name,
                            )}
                          </>
                        ) : null}
                      </p>
                      {artifact.note ? <span>{artifact.note}</span> : null}
                    </div>
                  </article>
                ))}
              </div>
            </section>
          </div>

          <div className="universe-state-notes">
            {data.universeState.notes.map((note) => (
              <p key={note}>{note}</p>
            ))}
          </div>
        </section>

        <section className="timeline-shell detail-panel">
          <header className="timeline-header detail-panel-header">
            <div>
              <p className="section-kicker">Dependencies</p>
              <h2>Events that lead here</h2>
            </div>
            <p className="timeline-caption">
              Showing browser-fetched causal ancestors at hop depth <code>{dependencyDepth}</code> from
              <code> /dependencies?depth={dependencyDepth}</code>.
            </p>
          </header>
          <form className="detail-toolbar" method="get" onSubmit={handleDependencyDepthSubmit}>
            <label className="filter-field">
              <span>Traversal depth</span>
              <select
                name="depth"
                value={dependencyDepthDraft}
                onChange={(event) => setDependencyDepthDraft(event.target.value)}
              >
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
          {isDependencyLoading ? (
            <p className="detail-empty">Updating dependencies…</p>
          ) : dependencyError ? (
            <p className="detail-empty">{dependencyError}</p>
          ) : renderEventList(
              dependencyItems ?? data.dependencies,
              `No upstream dependencies found at hop depth ${dependencyDepth}.`,
            )}
        </section>

        <section className="timeline-shell detail-panel">
          <header className="timeline-header detail-panel-header">
            <div>
              <p className="section-kicker">Consequences</p>
              <h2>Events that follow from this</h2>
            </div>
            <p className="timeline-caption">
              Showing browser-fetched downstream effects at hop depth <code>{consequenceDepth}</code> from
              <code> /consequences?depth={consequenceDepth}</code>.
            </p>
          </header>
          <form className="detail-toolbar" method="get" onSubmit={handleConsequenceDepthSubmit}>
            <label className="filter-field">
              <span>Traversal depth</span>
              <select
                name="depth"
                value={consequenceDepthDraft}
                onChange={(event) => setConsequenceDepthDraft(event.target.value)}
              >
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
          {isConsequenceLoading ? (
            <p className="detail-empty">Updating consequences…</p>
          ) : consequenceError ? (
            <p className="detail-empty">{consequenceError}</p>
          ) : renderEventList(
              consequenceItems ?? data.consequences,
              `No downstream consequences found at hop depth ${consequenceDepth}.`,
            )}
        </section>
      </section>
    </main>
  );
}
