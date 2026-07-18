from __future__ import annotations

import json
from pathlib import Path

import yaml

from benchmark.importers.swe_bench_snapshot import load_selection, materialize_snapshot
from benchmark.validate_tasks import load_schema, validate_file


def _records() -> list[dict[str, str]]:
    return [
        {
            "instance_id": "owner__repo-1",
            "repo": "owner/repo",
            "base_commit": "abc123",
            "problem_statement": "Fix issue one.",
            "patch": "SECRET",
        },
        {
            "instance_id": "owner__repo-2",
            "repo": "owner/repo",
            "base_commit": "def456",
            "problem_statement": "Fix issue two.",
            "test_patch": "SECRET TEST",
        },
    ]


def test_load_selection_rejects_duplicates(tmp_path: Path) -> None:
    path = tmp_path / "selection.yaml"
    path.write_text("instance_ids:\n  - a\n  - a\n", encoding="utf-8")
    try:
        load_selection(path)
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate selections should fail")


def test_materialization_is_deterministic_and_records_revision(tmp_path: Path) -> None:
    selection = ["owner__repo-2", "owner__repo-1"]

    def resolver(dataset: str, revision: str) -> str:
        assert dataset == "dataset/name"
        assert revision == "release-v1"
        return "deadbeef"

    def loader(dataset: str, revision: str, split: str):
        assert revision == "deadbeef"
        assert split == "test"
        return reversed(_records())

    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_snapshot = tmp_path / "first.json"
    second_snapshot = tmp_path / "second.json"

    first, snapshot = materialize_snapshot(
        dataset_name="dataset/name",
        requested_revision="release-v1",
        split="test",
        selection=selection,
        output_dir=first_dir,
        snapshot_path=first_snapshot,
        resolver=resolver,
        loader=loader,
    )
    second, _ = materialize_snapshot(
        dataset_name="dataset/name",
        requested_revision="release-v1",
        split="test",
        selection=selection,
        output_dir=second_dir,
        snapshot_path=second_snapshot,
        resolver=resolver,
        loader=loader,
    )

    assert first_snapshot.read_bytes() == second_snapshot.read_bytes()
    assert [path.name for path in first] == [path.name for path in second]
    assert snapshot["resolved_revision"] == "deadbeef"
    for first_path, second_path in zip(first, second, strict=True):
        assert first_path.read_bytes() == second_path.read_bytes()
        assert validate_file(first_path, load_schema()) == []
        task = yaml.safe_load(first_path.read_text(encoding="utf-8"))
        assert task["metadata"]["dataset_revision"] == "deadbeef"
        rendered = first_path.read_text(encoding="utf-8")
        assert "SECRET" not in rendered


def test_missing_selected_instance_is_actionable(tmp_path: Path) -> None:
    try:
        materialize_snapshot(
            dataset_name="dataset/name",
            requested_revision="revision",
            split="test",
            selection=["missing"],
            output_dir=tmp_path / "out",
            snapshot_path=tmp_path / "snapshot.json",
            resolver=lambda _dataset, _revision: "sha",
            loader=lambda _dataset, _revision, _split: _records(),
        )
    except ValueError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("missing selected instances should fail")


def test_snapshot_contains_no_time_dependent_fields(tmp_path: Path) -> None:
    materialize_snapshot(
        dataset_name="dataset/name",
        requested_revision="revision",
        split="test",
        selection=["owner__repo-1"],
        output_dir=tmp_path / "out",
        snapshot_path=tmp_path / "snapshot.json",
        resolver=lambda _dataset, _revision: "sha",
        loader=lambda _dataset, _revision, _split: _records(),
    )
    snapshot = json.loads((tmp_path / "snapshot.json").read_text(encoding="utf-8"))
    assert "created_at" not in snapshot
