import type { Route } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getFactionBySlug } from "../../../lib/holocron-api";

type FactionDetailPageProps = {
  params: Promise<{
    slug: string;
  }>;
};

export default async function FactionDetailPage({ params }: FactionDetailPageProps) {
  const { slug } = await params;

  try {
    const faction = await getFactionBySlug(slug);

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
            <span className="detail-slug">/{faction.slug}</span>
          </div>

          <h1>{faction.name}</h1>
          <p className="detail-description">{faction.description ?? "No description available."}</p>

          <div className="hero-stats detail-stats">
            <div className="stat-card">
              <span className="stat-label">Registry status</span>
              <strong>Indexed in graph</strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">Entity class</span>
              <strong>Faction</strong>
            </div>
          </div>
        </section>
      </main>
    );
  } catch {
    notFound();
  }
}
