from __future__ import annotations

import argparse
from pathlib import Path

from app.core.config import get_settings
from app.ingestion.transformer import load_processed_dataset, transform_raw_directory, write_processed_dataset


def transform_main() -> int:
    parser = argparse.ArgumentParser(description="Transform raw contributor data into a canonical processed dataset.")
    parser.add_argument("--raw-dir", default="data/raw", help="Directory containing raw dataset JSON files.")
    parser.add_argument(
        "--output",
        default="data/processed/dataset.json",
        help="Destination path for the processed dataset JSON file.",
    )
    args = parser.parse_args()

    dataset = transform_raw_directory(Path(args.raw_dir))
    write_processed_dataset(dataset, Path(args.output))
    print(
        "[TRANSFORM]"
        f" events={len(dataset.events)}"
        f" characters={len(dataset.characters)}"
        f" planets={len(dataset.planets)}"
        f" factions={len(dataset.factions)}"
        f" relationships={len(dataset.relationships)}"
    )
    print(f"[OUTPUT] {Path(args.output)}")
    return 0


def ingest_main() -> int:
    from neo4j import GraphDatabase

    from app.engine.services.character_service import CharacterService
    from app.engine.services.event_service import EventService
    from app.engine.services.faction_service import FactionService
    from app.engine.services.planet_service import PlanetService
    from app.engine.services.relationship_service import RelationshipService
    from app.ingestion.importer import DatasetImporter
    from app.repositories.neo4j.character_repository import Neo4jCharacterRepository
    from app.repositories.neo4j.event_repository import Neo4jEventRepository
    from app.repositories.neo4j.faction_repository import Neo4jFactionRepository
    from app.repositories.neo4j.graph_repository import Neo4jGraphRepository
    from app.repositories.neo4j.planet_repository import Neo4jPlanetRepository

    parser = argparse.ArgumentParser(description="Ingest a processed dataset into Neo4j through backend services.")
    parser.add_argument(
        "--input",
        default="data/processed/dataset.json",
        help="Path to the processed dataset JSON file.",
    )
    args = parser.parse_args()

    dataset = load_processed_dataset(Path(args.input))
    settings = get_settings()
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )
    try:
        importer = DatasetImporter(
            event_service=EventService(Neo4jEventRepository(driver=driver, settings=settings)),
            character_service=CharacterService(Neo4jCharacterRepository(driver=driver, settings=settings)),
            planet_service=PlanetService(Neo4jPlanetRepository(driver=driver, settings=settings)),
            faction_service=FactionService(Neo4jFactionRepository(driver=driver, settings=settings)),
            relationship_service=RelationshipService(Neo4jGraphRepository(driver=driver, settings=settings)),
        )
        result = importer.import_dataset(dataset)
    finally:
        driver.close()

    print(
        "[INGEST]"
        f" events(created={result.events.created}, skipped={result.events.skipped})"
        f" characters(created={result.characters.created}, skipped={result.characters.skipped})"
        f" planets(created={result.planets.created}, skipped={result.planets.skipped})"
        f" factions(created={result.factions.created}, skipped={result.factions.skipped})"
        f" relationships(created={result.relationships.created}, skipped={result.relationships.skipped})"
    )
    return 0
