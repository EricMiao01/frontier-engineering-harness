from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

import yaml

REQUIRED_FIELDS = ("instance_id", "repo", "base_commit", "problem_statement")


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ValueError("instance_id cannot be normalized to a task id")
    return slug


def _repo_url(repo: str) -> str:
    value = repo.strip()
    if value.startswith(("https://", "http://", "ssh://", "git://", "git@", "file://")):
        return value
    if value.count("/") != 1:
        raise ValueError(f"repo must be owner/name or a Git URL: {repo!r}")
    return f"https://github.com/{value}.git"


def load_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        payload = json.loads(text)
        records = payload if isinstance(payload, list) else [payload]
    if not all(isinstance(record, dict) for record in records):
        raise ValueError("input must contain JSON objects")
    return records


def convert_record(
    record: dict[str, Any],
    *,
    dataset_name: str,
    dataset_revision: str | None = None,
) -> dict[str, Any]:
    missing = [field for field in REQUIRED_FIELDS if not isinstance(record.get(field), str) or not record[field].strip()]
    if missing:
        raise ValueError(f"missing required SWE-bench fields: {', '.join(missing)}")

    instance_id = record["instance_id"].strip()
    repo = record["repo"].strip()
    metadata: dict[str, Any] = {
        "dataset": dataset_name,
        "dataset_schema": "swe-bench-v1",
        "instance_id": instance_id,
        "original_repo": repo,
        "official_evaluation_required": True,
    }
    if dataset_revision:
        metadata["dataset_revision"] = dataset_revision

    task = {
        "id": _slug(instance_id),
        "version": 1,
        "source": "public_import",
        "category": "difficult_bug",
        "difficulty": "hard",
        "repository": {
            "source": _repo_url(repo),
            "base_commit": record["base_commit"].strip(),
        },
        "prompt": record["problem_statement"].strip(),
        "constraints": [
            "Preserve unrelated behavior and public APIs unless the issue requires otherwise.",
            "Do not use or reconstruct the benchmark gold patch.",
        ],
        "acceptance": [
            "The reported issue is resolved without regressing relevant existing behavior.",
            "The solution passes the official SWE-bench evaluation for this instance.",
        ],
        "process_expectations": {
            "reproduction_required": True,
            "clarification_required": False,
            "specification_required": False,
            "regression_test_required": True,
            "root_cause_required": True,
        },
        "routing_expectations": {
            "mode": "selective_skills",
            "useful_skills": ["explore", "diagnose", "verify"],
        },
        "graders": [{"type": "diff_scope", "allowed_paths": ["."]}],
        "budgets": {
            "max_steps": 200,
            "max_tokens": 200000,
            "max_wall_seconds": 7200,
        },
        "metadata": metadata,
    }
    for field in ("version", "created_at", "environment_setup_commit"):
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            task["metadata"][f"swe_bench_{field}"] = value.strip()
    return task


def import_records(
    records: Iterable[dict[str, Any]],
    output_dir: Path,
    *,
    dataset_name: str,
    dataset_revision: str | None = None,
    instance_ids: set[str] | None = None,
    limit: int | None = None,
) -> list[Path]:
    selected = []
    for record in records:
        if instance_ids and record.get("instance_id") not in instance_ids:
            continue
        selected.append(record)
        if limit is not None and len(selected) >= limit:
            break

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for record in sorted(selected, key=lambda item: str(item.get("instance_id", ""))):
        task = convert_record(record, dataset_name=dataset_name, dataset_revision=dataset_revision)
        path = output_dir / f"{task['id']}.yaml"
        path.write_text(yaml.safe_dump(task, sort_keys=False, allow_unicode=True), encoding="utf-8")
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import SWE-bench JSON/JSONL records into canonical task YAML.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--dataset-name", default="princeton-nlp/SWE-bench_Verified")
    parser.add_argument("--dataset-revision")
    parser.add_argument("--instance-id", action="append", default=[])
    parser.add_argument("--limit", type=int)
    args = parser.parse_args(argv)

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    written = import_records(
        load_records(args.input),
        args.output_dir,
        dataset_name=args.dataset_name,
        dataset_revision=args.dataset_revision,
        instance_ids=set(args.instance_id) or None,
        limit=args.limit,
    )
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
