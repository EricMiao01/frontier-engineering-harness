from __future__ import annotations

import json
from pathlib import Path

import yaml

from benchmark.importers.swe_bench import convert_record, import_records, load_records
from benchmark.validate_tasks import load_schema, validate_file


def _record(instance_id: str = "sympy__sympy-20590") -> dict[str, str]:
    return {
        "instance_id": instance_id,
        "repo": "sympy/sympy",
        "base_commit": "0123456789abcdef",
        "problem_statement": "Correct a regression in symbolic simplification.",
        "patch": "SECRET GOLD PATCH",
        "test_patch": "SECRET TEST PATCH",
        "version": "1.7",
    }


def test_convert_record_maps_required_fields_without_gold_patch() -> None:
    task = convert_record(_record(), dataset_name="princeton-nlp/SWE-bench_Verified")

    assert task["id"] == "sympy-sympy-20590"
    assert task["repository"] == {
        "source": "https://github.com/sympy/sympy.git",
        "base_commit": "0123456789abcdef",
    }
    assert task["prompt"] == "Correct a regression in symbolic simplification."
    rendered = yaml.safe_dump(task)
    assert "SECRET GOLD PATCH" not in rendered
    assert "SECRET TEST PATCH" not in rendered


def test_import_is_byte_stable_and_schema_valid(tmp_path: Path) -> None:
    records = [_record("sympy__sympy-20590"), _record("sympy__sympy-20600")]
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_paths = import_records(records, first, dataset_name="dataset", limit=1)
    second_paths = import_records(records, second, dataset_name="dataset", limit=1)

    assert first_paths[0].read_bytes() == second_paths[0].read_bytes()
    assert validate_file(first_paths[0], load_schema()) == []


def test_filter_selects_requested_instance(tmp_path: Path) -> None:
    paths = import_records(
        [_record("owner__repo-1"), _record("owner__repo-2")],
        tmp_path,
        dataset_name="dataset",
        instance_ids={"owner__repo-2"},
    )
    assert [path.name for path in paths] == ["owner-repo-2.yaml"]


def test_load_json_and_jsonl(tmp_path: Path) -> None:
    json_path = tmp_path / "records.json"
    jsonl_path = tmp_path / "records.jsonl"
    json_path.write_text(json.dumps([_record()]), encoding="utf-8")
    jsonl_path.write_text(json.dumps(_record()) + "\n", encoding="utf-8")

    assert len(load_records(json_path)) == 1
    assert len(load_records(jsonl_path)) == 1


def test_missing_required_field_is_rejected() -> None:
    record = _record()
    del record["base_commit"]

    try:
        convert_record(record, dataset_name="dataset")
    except ValueError as exc:
        assert "base_commit" in str(exc)
    else:
        raise AssertionError("missing base_commit should fail")
