import type { Route } from "next";
import Link from "next/link";

import { getFactions } from "../../lib/holocron-api";

export default async function FactionsPage() {
  const factions = await getFactions();

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
      </section>

      <section className="timeline-shell entity-shell">
        <header className="timeline-header entity-header">
          <div>
            <p className="section-kicker">Power blocs</p>
            <h2>Known factions</h2>
          </div>
          <p className="timeline-caption">
            Each faction profile is sourced from <code>/api/v1/factions</code>.
          </p>
        </header>
        <div className="entity-grid">
          {factions.map((faction) => (
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
