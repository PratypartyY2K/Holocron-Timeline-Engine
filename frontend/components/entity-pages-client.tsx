"use client";

import type { Route } from "next";
import Link from "next/link";
import { ArchiveSearchNav } from "./archive-search-nav";
import {
  type CharacterRecord,
  type EventRecord,
  type FactionDetailResponse,
  formatEventRange,
  getCharacterBySlug,
  getCharacterTimeline,
  getCharacters,
  getFactionDetailBySlug,
  getFactions,
  getPlanetBySlug,
  getPlanets,
} from "../lib/holocron-api";
import { useAsyncData } from "../lib/use-async-data";
import { ErrorPageFeedback, LoadingPageFeedback } from "./page-feedback";

type EntitySlugProps = {
  slug: string;
};

function renderRelatedCharacters(items: CharacterRecord[], emptyLabel: string) {
  if (items.length === 0) {
    return <p className="detail-empty">{emptyLabel}</p>;
  }

  return (
    <div className="entity-grid">
      {items.map((character) => (
        <Link
          key={character.id}
          href={`/characters/${character.slug}` as Route}
          className="entity-card"
        >
          <div className="entity-card-meta">
            <span>{character.species ?? "Unknown species"}</span>
            <span>{character.homeworld_name ?? "Unknown homeworld"}</span>
          </div>
          <h3>{character.name}</h3>
          <p>{character.description ?? "No description available."}</p>
        </Link>
      ))}
    </div>
  );
}

function renderRelatedFactions(items: FactionDetailResponse["enemy_factions"], emptyLabel: string) {
  if (items.length === 0) {
    return <p className="detail-empty">{emptyLabel}</p>;
  }

  return (
    <div className="entity-grid">
      {items.map((faction) => (
        <Link
          key={faction.id}
          href={`/factions/${faction.slug}` as Route}
          className="entity-card"
        >
          <div className="entity-card-meta">
            <span>Enemy faction</span>
            <span>/{faction.slug}</span>
          </div>
          <h3>{faction.name}</h3>
          <p>{faction.description ?? "No description available."}</p>
        </Link>
      ))}
    </div>
  );
}

function renderRelatedEvents(items: EventRecord[], emptyLabel: string) {
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

export function CharactersPageClient() {
  const { data, error, isLoading } = useAsyncData(getCharacters, []);

  if (isLoading) {
    return (
      <LoadingPageFeedback
        title="Character directory"
        message="Loading character records from the browser."
      />
    );
  }

  if (error || !data) {
    return (
      <ErrorPageFeedback
        title="Character directory"
        message={error ?? "Characters could not be loaded."}
      />
    );
  }

  return (
    <main className="page-shell">
      <section className="hero detail-hero">
        <div className="detail-breadcrumb-row">
          <Link href={"/" as Route} className="back-link">
            ← Back to archive
          </Link>
          <span className="detail-chip">Characters</span>
        </div>
        <h1>Character directory</h1>
        <p className="detail-description">
          Browse named individuals and their node profiles, then pivot into event history
          through character-aware timeline filters.
        </p>
        <ArchiveSearchNav />
      </section>

      <section className="timeline-shell entity-shell">
        <header className="timeline-header entity-header">
          <div>
            <p className="section-kicker">Personae</p>
            <h2>Known characters</h2>
          </div>
          <p className="timeline-caption">
            Each profile is fetched in the browser from <code>/api/v1/characters</code>.
          </p>
        </header>
        <div className="entity-grid">
          {data.map((character) => (
            <Link
              key={character.id}
              href={`/characters/${character.slug}` as Route}
              className="entity-card"
            >
              <div className="entity-card-meta">
                <span>{character.species ?? "Unknown species"}</span>
                <span>{character.homeworld_name ?? "Unknown homeworld"}</span>
              </div>
              <h3>{character.name}</h3>
              <p>{character.description ?? "No description available."}</p>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}

export function CharacterDetailPageClient({ slug }: EntitySlugProps) {
  const { data, error, isLoading } = useAsyncData(
    async () => {
      const character = await getCharacterBySlug(slug);
      const timeline = await getCharacterTimeline(character.id, {
        limit: 12,
        order: "asc",
      });
      return {
        character,
        timeline,
      };
    },
    [slug],
  );

  if (isLoading) {
    return (
      <LoadingPageFeedback
        title="Character profile"
        message="Loading character data from the browser."
      />
    );
  }

  if (error || !data) {
    return (
      <ErrorPageFeedback
        title="Character profile"
        message={error ?? "Character data could not be loaded."}
      />
    );
  }

  return (
    <main className="page-shell">
      <section className="hero detail-hero">
        <div className="detail-breadcrumb-row">
          <Link href={"/characters" as Route} className="back-link">
            ← Back to characters
          </Link>
          <span className="detail-chip">{data.character.species ?? "Unknown species"}</span>
        </div>

        <div className="detail-meta">
          <span className="detail-slug">/{data.character.slug}</span>
          <span className="timeline-era">{data.character.homeworld_name ?? "No homeworld on record"}</span>
        </div>

        <h1>{data.character.name}</h1>
        <p className="detail-description">{data.character.description ?? "No description available."}</p>
        <ArchiveSearchNav />

        <div className="hero-stats detail-stats">
          <div className="stat-card">
            <span className="stat-label">Species</span>
            <strong>{data.character.species ?? "Unknown"}</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Homeworld</span>
            <strong>{data.character.homeworld_name ?? "Unlisted"}</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Timeline hits</span>
            <strong>{data.timeline.total} related events</strong>
          </div>
        </div>
      </section>

      <section className="timeline-shell entity-shell">
        <header className="timeline-header entity-header">
          <div>
            <p className="section-kicker">Related chronology</p>
            <h2>Events involving {data.character.name}</h2>
          </div>
          <p className="timeline-caption">
            Browser-fetched from <code>/api/v1/characters/{data.character.id}/timeline</code>.
          </p>
        </header>
        <div className="detail-list">
          {data.timeline.items.length === 0 ? (
            <p className="detail-empty">No timeline events reference this character yet.</p>
          ) : (
            data.timeline.items.map((event) => (
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
            ))
          )}
        </div>
        <div className="entity-footer">
          <Link href={`/?character=${data.character.slug}` as Route} className="secondary-link">
            Open main timeline filters
          </Link>
        </div>
      </section>
    </main>
  );
}

export function PlanetsPageClient() {
  const { data, error, isLoading } = useAsyncData(getPlanets, []);

  if (isLoading) {
    return (
      <LoadingPageFeedback
        title="Planetary atlas"
        message="Loading planet records from the browser."
      />
    );
  }

  if (error || !data) {
    return (
      <ErrorPageFeedback
        title="Planetary atlas"
        message={error ?? "Planets could not be loaded."}
      />
    );
  }

  return (
    <main className="page-shell">
      <section className="hero detail-hero">
        <div className="detail-breadcrumb-row">
          <Link href={"/" as Route} className="back-link">
            ← Back to archive
          </Link>
          <span className="detail-chip">Planets</span>
        </div>
        <h1>Planetary atlas</h1>
        <p className="detail-description">
          Browse worlds across the galaxy, inspect their profile metadata, and pivot into
          timeline events anchored to each location.
        </p>
        <ArchiveSearchNav />
      </section>

      <section className="timeline-shell entity-shell">
        <header className="timeline-header entity-header">
          <div>
            <p className="section-kicker">Atlas</p>
            <h2>Known planets</h2>
          </div>
          <p className="timeline-caption">
            Each world profile is fetched in the browser from <code>/api/v1/planets</code>.
          </p>
        </header>
        <div className="entity-grid">
          {data.map((planet) => (
            <Link
              key={planet.id}
              href={`/planets/${planet.slug}` as Route}
              className="entity-card"
            >
              <div className="entity-card-meta">
                <span>{planet.region ?? "Unknown region"}</span>
                <span>/{planet.slug}</span>
              </div>
              <h3>{planet.name}</h3>
              <p>{planet.description ?? "No description available."}</p>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}

export function PlanetDetailPageClient({ slug }: EntitySlugProps) {
  const { data, error, isLoading } = useAsyncData(() => getPlanetBySlug(slug), [slug]);

  if (isLoading) {
    return (
      <LoadingPageFeedback
        title="Planet profile"
        message="Loading planet data from the browser."
      />
    );
  }

  if (error || !data) {
    return (
      <ErrorPageFeedback
        title="Planet profile"
        message={error ?? "Planet data could not be loaded."}
      />
    );
  }

  return (
    <main className="page-shell">
      <section className="hero detail-hero">
        <div className="detail-breadcrumb-row">
          <Link href={"/planets" as Route} className="back-link">
            ← Back to planets
          </Link>
          <span className="detail-chip">{data.region ?? "Unknown region"}</span>
        </div>

        <div className="detail-meta">
          <span className="detail-slug">/{data.slug}</span>
        </div>

        <h1>{data.name}</h1>
        <p className="detail-description">{data.description ?? "No description available."}</p>
        <ArchiveSearchNav />

        <div className="hero-stats detail-stats">
          <div className="stat-card">
            <span className="stat-label">Region</span>
            <strong>{data.region ?? "Unknown"}</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Timeline lookup</span>
            <strong>Location-aware event filter</strong>
          </div>
        </div>
      </section>

      <section className="timeline-shell entity-shell">
        <header className="timeline-header entity-header">
          <div>
            <p className="section-kicker">Related chronology</p>
            <h2>Events at {data.name}</h2>
          </div>
          <p className="timeline-caption">
            Jump into <code>/api/v1/events?location={data.slug}</code> from the main timeline.
          </p>
        </header>
        <div className="entity-footer">
          <Link href={`/?location=${data.slug}` as Route} className="action-button">
            View filtered timeline
          </Link>
        </div>
      </section>
    </main>
  );
}

export function FactionsPageClient() {
  const { data, error, isLoading } = useAsyncData(getFactions, []);

  if (isLoading) {
    return (
      <LoadingPageFeedback
        title="Faction registry"
        message="Loading faction records from the browser."
      />
    );
  }

  if (error || !data) {
    return (
      <ErrorPageFeedback
        title="Faction registry"
        message={error ?? "Factions could not be loaded."}
      />
    );
  }

  return (
    <main className="page-shell">
      <section className="hero detail-hero">
        <div className="detail-breadcrumb-row">
          <Link href={"/" as Route} className="back-link">
            ← Back to archive
          </Link>
          <span className="detail-chip">Factions</span>
        </div>
        <h1>Faction registry</h1>
        <p className="detail-description">
          Browse the major blocs in the graph and inspect the organizations shaping the
          galaxy-wide chronology.
        </p>
        <ArchiveSearchNav />
      </section>

      <section className="timeline-shell entity-shell">
        <header className="timeline-header entity-header">
          <div>
            <p className="section-kicker">Power blocs</p>
            <h2>Known factions</h2>
          </div>
          <p className="timeline-caption">
            Each faction profile is fetched in the browser from <code>/api/v1/factions</code>.
          </p>
        </header>
        <div className="entity-grid">
          {data.map((faction) => (
            <Link
              key={faction.id}
              href={`/factions/${faction.slug}` as Route}
              className="entity-card"
            >
              <div className="entity-card-meta">
                <span>Faction profile</span>
                <span>/{faction.slug}</span>
              </div>
              <h3>{faction.name}</h3>
              <p>{faction.description ?? "No description available."}</p>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}

export function FactionDetailPageClient({ slug }: EntitySlugProps) {
  const { data, error, isLoading } = useAsyncData(() => getFactionDetailBySlug(slug), [slug]);

  if (isLoading) {
    return (
      <LoadingPageFeedback
        title="Faction profile"
        message="Loading faction data from the browser."
      />
    );
  }

  if (error || !data) {
    return (
      <ErrorPageFeedback
        title="Faction profile"
        message={error ?? "Faction data could not be loaded."}
      />
    );
  }

  return (
    <main className="page-shell">
      <section className="hero detail-hero">
        <div className="detail-breadcrumb-row">
          <Link href={"/factions" as Route} className="back-link">
            ← Back to factions
          </Link>
          <span className="detail-chip">Faction profile</span>
        </div>

        <div className="detail-meta">
          <span className="detail-slug">/{data.faction.slug}</span>
        </div>

        <h1>{data.faction.name}</h1>
        <p className="detail-description">{data.faction.description ?? "No description available."}</p>
        <ArchiveSearchNav />

        <div className="hero-stats detail-stats">
          <div className="stat-card">
            <span className="stat-label">Registry status</span>
            <strong>Indexed in graph</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Entity class</span>
            <strong>Faction</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Associated characters</span>
            <strong>{data.characters.length}</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Enemy factions</span>
            <strong>{data.enemy_factions.length}</strong>
          </div>
        </div>
      </section>

      <section className="timeline-shell entity-shell">
        <header className="timeline-header entity-header">
          <div>
            <p className="section-kicker">Affiliates</p>
            <h2>Characters aligned with {data.faction.name}</h2>
          </div>
          <p className="timeline-caption">
            Derived from characters co-involved in events tagged to this faction.
          </p>
        </header>
        {renderRelatedCharacters(
          data.characters,
          `No associated characters found for ${data.faction.name}.`,
        )}
      </section>

      <section className="timeline-shell entity-shell">
        <header className="timeline-header entity-header">
          <div>
            <p className="section-kicker">Opposition</p>
            <h2>Enemy factions</h2>
          </div>
          <p className="timeline-caption">
            Loaded from direct <code>ENEMY_OF</code> graph relationships.
          </p>
        </header>
        {renderRelatedFactions(
          data.enemy_factions,
          `No enemy factions recorded for ${data.faction.name}.`,
        )}
      </section>

      <section className="timeline-shell entity-shell">
        <header className="timeline-header entity-header">
          <div>
            <p className="section-kicker">Chronology</p>
            <h2>Events involving {data.faction.name}</h2>
          </div>
          <p className="timeline-caption">
            Browser-fetched from <code>/api/v1/factions/by-slug/{data.faction.slug}/detail</code>.
          </p>
        </header>
        {renderRelatedEvents(
          data.involved_events,
          `No events found involving ${data.faction.name}.`,
        )}
      </section>
    </main>
  );
}
