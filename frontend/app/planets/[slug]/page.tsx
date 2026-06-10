import type { Route } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getPlanetBySlug } from "../../../lib/holocron-api";

type PlanetDetailPageProps = {
  params: Promise<{
    slug: string;
  }>;
};

export default async function PlanetDetailPage({ params }: PlanetDetailPageProps) {
  const { slug } = await params;

  try {
    const planet = await getPlanetBySlug(slug);

    return (
      <main className="page-shell">
        <section className="hero detail-hero">
          <div className="detail-breadcrumb-row">
            <Link href={"/planets" as Route} className="back-link">
              ← Back to planets
            </Link>
            <span className="detail-chip">{planet.region ?? "Unknown region"}</span>
          </div>

          <div className="detail-meta">
            <span className="detail-slug">/{planet.slug}</span>
          </div>

          <h1>{planet.name}</h1>
          <p className="detail-description">{planet.description ?? "No description available."}</p>

          <div className="hero-stats detail-stats">
            <div className="stat-card">
              <span className="stat-label">Region</span>
              <strong>{planet.region ?? "Unknown"}</strong>
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
              <h2>Events at {planet.name}</h2>
            </div>
            <p className="timeline-caption">
              Jump into <code>/api/v1/events?location={planet.slug}</code> from the main timeline.
            </p>
          </header>
          <div className="entity-footer">
            <Link href={`/?location=${planet.slug}` as Route} className="action-button">
              View filtered timeline
            </Link>
          </div>
        </section>
      </main>
    );
  } catch {
    notFound();
  }
}
