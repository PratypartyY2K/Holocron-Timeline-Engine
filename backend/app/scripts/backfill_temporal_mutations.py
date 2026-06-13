import argparse

from app.core.config import get_settings
from app.engine.services.relationship_service import RelationshipService
from app.engine.services.temporal_mutation_backfill_service import TemporalMutationBackfillService
from app.repositories.neo4j.character_repository import Neo4jCharacterRepository
from app.repositories.neo4j.event_repository import Neo4jEventRepository
from app.repositories.neo4j.faction_repository import Neo4jFactionRepository
from app.repositories.neo4j.graph_repository import Neo4jGraphRepository
from app.repositories.neo4j.planet_repository import Neo4jPlanetRepository
from app.scripts.neo4j_uri import normalize_cli_neo4j_uri
from neo4j import GraphDatabase


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill curated temporal mutation edges into Neo4j using backend services."
    )
    parser.add_argument("--dry-run", action="store_true", help="Plan mutations without writing them")
    parser.add_argument(
        "--neo4j-uri",
        default=None,
        help="Optional Neo4j URI override. Defaults to backend settings, with local CLI normalization from neo4j to localhost.",
    )
    args = parser.parse_args()

    settings = get_settings().model_copy(
        update={
            "neo4j_uri": normalize_cli_neo4j_uri(args.neo4j_uri or get_settings().neo4j_uri),
        }
    )
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )
    event_repository = Neo4jEventRepository(driver=driver, settings=settings)
    character_repository = Neo4jCharacterRepository(driver=driver, settings=settings)
    planet_repository = Neo4jPlanetRepository(driver=driver, settings=settings)
    faction_repository = Neo4jFactionRepository(driver=driver, settings=settings)
    graph_repository = Neo4jGraphRepository(driver=driver, settings=settings)
    relationship_service = RelationshipService(graph_repository=graph_repository)
    backfill_service = TemporalMutationBackfillService(
        event_repository=event_repository,
        character_repository=character_repository,
        planet_repository=planet_repository,
        faction_repository=faction_repository,
        relationship_service=relationship_service,
    )

    try:
        result = backfill_service.backfill(dry_run=args.dry_run)
    finally:
        driver.close()

    mode = "DRY RUN" if args.dry_run else "APPLY"
    print(f"[NEO4J URI] {settings.neo4j_uri}")
    print(f"[{mode}] planned={result.planned} applied={result.applied} skipped_duplicates={result.skipped_duplicates}")
    for missing_event in result.missing_events:
        print(f"[MISSING EVENT] {missing_event}")
    for skipped_entity in result.skipped_missing_entities:
        print(f"[SKIPPED ENTITY] {skipped_entity}")
    for detail in result.details:
        print(f"[PLAN] {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
