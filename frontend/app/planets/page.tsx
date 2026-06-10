import type { Route } from "next";
import Link from "next/link";

import { getPlanets } from "../../lib/holocron-api";

export default async function PlanetsPage() {
  const planets = await getPlanets();

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
      </section>

      <section className="timeline-shell entity-shell">
        <header className="timeline-header entity-header">
          <div>
            <p className="section-kicker">Atlas</p>
            <h2>Known planets</h2>
          </div>
          <p className="timeline-caption">
            Each world profile is sourced from <code>/api/v1/planets</code>.
          </p>
        </header>
        <div className="entity-grid">
          {planets.map((planet) => (
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
