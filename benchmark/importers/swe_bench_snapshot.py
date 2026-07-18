from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable, Iterable

import yaml

from benchmark.importers.swe_bench import import_records

Resolver = Callable[[str, str], str]
Loader = Callable[[str, str, str], Iterable[dict[str, Any]]]


def load_selection(path: Path) -> list[str]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("instance_ids"), list):
        raise ValueError("selection must contain an instance_ids list")
    instance_ids = payload["instance_ids"]
    if not instance_ids or not all(isinstance(value, str) and value.strip() for value in instance_ids):
        raise ValueError("selection instance_ids must be non-empty strings")
    normalized = [value.strip() for value in instance_ids]
    if len(set(normalized)) != len(normalized):
        raise ValueError("selection contains duplicate instance IDs")
    return normalized


def _default_resolver(dataset_name: str, revision: str) -> str:
    try:
        from huggingface_hub import HfApi
    except ImportError as exc:
        raise RuntimeError("huggingface_hub is required for snapshot materialization") from exc
    info = HfApi().dataset_info(dataset_name, revision=revision)
    if not info.sha:
        raise RuntimeError("dataset revision did not resolve to an immutable SHA")
    return info.sha


def _default_loader(dataset_name: str, revision: str, split: str) -> Iterable[dict[str, Any]]:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError("datasets is required for snapshot materialization") from exc
    return load_dataset(dataset_name, split=split, revision=revision)


def materialize_snapshot(
    *,
    dataset_name: str,
    requested_revision: str,
    split: str,
    selection: list[str],
    output_dir: Path,
    snapshot_path: Path,
    resolver: Resolver = _default_resolver,
    loader: Loader = _default_loader,
) -> tuple[list[Path], dict[str, Any]]:
    if not requested_revision.strip():
        raise ValueError("requested revision must be explicit")
    resolved_revision = resolver(dataset_name, requested_revision.strip())
    selected_set = set(selection)
    records = [record for record in loader(dataset_name, resolved_revision, split) if record.get("instance_id") in selected_set]
    found = {str(record.get("instance_id")) for record in records}
    missing = [instance_id for instance_id in selection if instance_id not in found]
    if missing:
        raise ValueError(f"selected SWE-bench instances were not found: {', '.join(missing)}")

    written = import_records(
        records,
        output_dir,
        dataset_name=dataset_name,
        dataset_revision=resolved_revision,
        instance_ids=selected_set,
    )
    snapshot = {
        "schema_version": 1,
        "dataset": dataset_name,
        "split": split,
        "requested_revision": requested_revision.strip(),
        "resolved_revision": resolved_revision,
        "instance_ids": selection,
        "manifest_files": [path.name for path in written],
    }
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return written, snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize a pinned SWE-bench subset.")
    parser.add_argument("--dataset-name", default="princeton-nlp/SWE-bench_Verified")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--split", default="test")
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    args = parser.parse_args(argv)

    written, _ = materialize_snapshot(
        dataset_name=args.dataset_name,
        requested_revision=args.revision,
        split=args.split,
        selection=load_selection(args.selection),
        output_dir=args.output_dir,
        snapshot_path=args.snapshot,
    )
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
