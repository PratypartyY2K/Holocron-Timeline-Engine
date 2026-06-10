import type { Route } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getCharacterBySlug } from "../../../lib/holocron-api";

type CharacterDetailPageProps = {
  params: Promise<{
    slug: string;
  }>;
};

export default async function CharacterDetailPage({ params }: CharacterDetailPageProps) {
  const { slug } = await params;

  try {
    const character = await getCharacterBySlug(slug);

    return (
      <main className="page-shell">
        <section className="hero detail-hero">
          <div className="detail-breadcrumb-row">
            <Link href={"/characters" as Route} className="back-link">
              ← Back to characters
            </Link>
            <span className="detail-chip">{character.species ?? "Unknown species"}</span>
          </div>

          <div className="detail-meta">
            <span className="detail-slug">/{character.slug}</span>
            <span className="timeline-era">{character.homeworld_name ?? "No homeworld on record"}</span>
          </div>

          <h1>{character.name}</h1>
          <p className="detail-description">{character.description ?? "No description available."}</p>

          <div className="hero-stats detail-stats">
            <div className="stat-card">
              <span className="stat-label">Species</span>
              <strong>{character.species ?? "Unknown"}</strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">Homeworld</span>
              <strong>{character.homeworld_name ?? "Unlisted"}</strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">Timeline lookup</span>
              <strong>Character-aware event filter</strong>
            </div>
          </div>
        </section>

        <section className="timeline-shell entity-shell">
          <header className="timeline-header entity-header">
            <div>
              <p className="section-kicker">Related chronology</p>
              <h2>Events involving {character.name}</h2>
            </div>
            <p className="timeline-caption">
              Jump into <code>/api/v1/events?character={character.slug}</code> from the main timeline.
            </p>
          </header>
          <div className="entity-footer">
            <Link href={`/?character=${character.slug}` as Route} className="action-button">
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
