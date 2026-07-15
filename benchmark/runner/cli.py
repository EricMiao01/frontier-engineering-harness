from __future__ import annotations

import argparse
import json
from pathlib import Path

from .runner import run_task


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one Frontier Engineering Harness benchmark task.")
    parser.add_argument("task", type=Path, help="Path to a benchmark task YAML file")
    parser.add_argument("--agent-command", required=True, help="Shell command used as the agent adapter")
    parser.add_argument("--output", type=Path, default=Path("run.json"), help="Run result JSON path")
    parser.add_argument("--workspace-root", type=Path, help="Optional persistent workspace root")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_task(
        args.task,
        args.agent_command,
        output_path=args.output,
        workspace_root=args.workspace_root,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
