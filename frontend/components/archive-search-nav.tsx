"use client";

import type { Route } from "next";
import Link from "next/link";

type ArchiveSearchNavProps = {
  defaultQuery?: string;
};

export function ArchiveSearchNav({ defaultQuery = "" }: ArchiveSearchNavProps) {
  return (
    <>
      <form className="search-bar" method="get" action="/events">
        <label className="search-field">
          <span className="search-label">Archive search</span>
          <input
            type="search"
            name="q"
            defaultValue={defaultQuery}
            placeholder="Search for Anakin, Order 66, Coruscant..."
          />
        </label>
        <button type="submit" className="action-button">
          Search archive
        </button>
      </form>
      <nav className="hero-nav" aria-label="Primary">
        <Link href={"/events" as Route} className="secondary-link">
          Events
        </Link>
        <Link href={"/characters" as Route} className="secondary-link">
          Characters
        </Link>
        <Link href={"/planets" as Route} className="secondary-link">
          Planets
        </Link>
        <Link href={"/factions" as Route} className="secondary-link">
          Factions
        </Link>
      </nav>
    </>
  );
}
