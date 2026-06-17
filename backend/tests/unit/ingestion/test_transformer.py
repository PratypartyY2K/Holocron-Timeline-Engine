import json

import pytest

from app.ingestion.transformer import load_processed_dataset, transform_raw_directory, write_processed_dataset


def test_transform_raw_directory_merges_and_sorts_records(tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "events.json").write_text(
        json.dumps(
            {
                "events": [
                    {
                        "slug": "battle-of-yavin",
                        "title": "Battle of Yavin",
                        "start_year": 0,
                        "end_year": 0,
                        "source_refs": ["ANH", "ANH"],
                    }
                ]
            }
        )
    )
    (raw_dir / "relationships.json").write_text(
        json.dumps(
            {
                "characters": [
                    {
                        "slug": "luke-skywalker",
                        "name": "Luke Skywalker",
                    }
                ],
                "relationships": [
                    {
                        "type": "INVOLVES",
                        "source": {"type": "event", "slug": "battle-of-yavin"},
                        "target": {"type": "character", "slug": "luke-skywalker"},
                        "note": "Primary pilot",
                    }
                ],
            }
        )
    )

    dataset = transform_raw_directory(raw_dir)

    assert [item.slug for item in dataset.events] == ["battle-of-yavin"]
    assert dataset.events[0].source_refs == ["ANH"]
    assert [item.slug for item in dataset.characters] == ["luke-skywalker"]
    assert dataset.relationships[0].source.slug == "battle-of-yavin"
    assert dataset.relationships[0].target.slug == "luke-skywalker"


def test_transform_raw_directory_rejects_conflicting_duplicate_slug(tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "first.json").write_text(json.dumps({"planets": [{"slug": "naboo", "name": "Naboo"}]}))
    (raw_dir / "second.json").write_text(json.dumps({"planets": [{"slug": "naboo", "name": "Theed"}]}))

    with pytest.raises(ValueError, match="Conflicting duplicate planet"):
        transform_raw_directory(raw_dir)


def test_write_and_load_processed_dataset_round_trip(tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "dataset.json").write_text(json.dumps({"factions": [{"slug": "rebel-alliance", "name": "Rebel Alliance"}]}))

    dataset = transform_raw_directory(raw_dir)
    destination = tmp_path / "processed" / "dataset.json"
    write_processed_dataset(dataset, destination)
    loaded = load_processed_dataset(destination)

    assert loaded == dataset
