import type { Route } from "next";
import Link from "next/link";

import { getCharacters } from "../../lib/holocron-api";

export default async function CharactersPage() {
  const characters = await getCharacters();

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
      </section>

      <section className="timeline-shell entity-shell">
        <header className="timeline-header entity-header">
          <div>
            <p className="section-kicker">Personae</p>
            <h2>Known characters</h2>
          </div>
          <p className="timeline-caption">
            Each profile is sourced from <code>/api/v1/characters</code>.
          </p>
        </header>
        <div className="entity-grid">
          {characters.map((character) => (
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
