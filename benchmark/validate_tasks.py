from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

DEFAULT_SCHEMA = Path(__file__).with_name("task.schema.json")
TASK_SUFFIXES = {".yaml", ".yml"}


@dataclass(frozen=True)
class ValidationIssue:
    file: Path
    field: str
    message: str

    def render(self) -> str:
        location = self.field or "<root>"
        return f"{self.file}: {location}: {self.message}"


def _format_path(parts: Iterable[Any]) -> str:
    result = ""
    for part in parts:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += ("." if result else "") + str(part)
    return result


def load_schema(path: Path = DEFAULT_SCHEMA) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        schema = json.load(handle)
    Draft202012Validator.check_schema(schema)
    return schema


def validate_file(path: Path, schema: dict[str, Any]) -> list[ValidationIssue]:
    try:
        with path.open(encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        return [ValidationIssue(path, "", f"unable to read YAML: {exc}")]

    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: list(error.absolute_path),
    )
    return [
        ValidationIssue(path, _format_path(error.absolute_path), error.message)
        for error in errors
    ]


def discover_task_files(paths: Iterable[Path]) -> list[Path]:
    discovered: set[Path] = set()
    for path in paths:
        if path.is_file() and path.suffix.lower() in TASK_SUFFIXES:
            discovered.add(path)
        elif path.is_dir():
            discovered.update(
                candidate
                for candidate in path.rglob("*")
                if candidate.is_file() and candidate.suffix.lower() in TASK_SUFFIXES
            )
    return sorted(discovered)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate benchmark task YAML files.")
    parser.add_argument("paths", nargs="+", type=Path, help="Task files or directories")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="JSON Schema path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    files = discover_task_files(args.paths)
    if not files:
        print("No YAML task files found.", file=sys.stderr)
        return 2

    schema = load_schema(args.schema)
    issues = [issue for file in files for issue in validate_file(file, schema)]
    if issues:
        for issue in issues:
            print(issue.render(), file=sys.stderr)
        print(f"FAILED: {len(issues)} validation error(s) across {len(files)} file(s).", file=sys.stderr)
        return 1

    print(f"OK: validated {len(files)} task file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
