from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from benchmark.validate_tasks import load_schema, validate_file


@dataclass(frozen=True)
class CommandResult:
    command: str
    exit_code: int | None
    duration_seconds: float
    stdout: str
    stderr: str
    timed_out: bool = False


@dataclass(frozen=True)
class GraderResult:
    type: str
    passed: bool
    command_result: CommandResult | None = None
    message: str | None = None


@dataclass
class RunResult:
    schema_version: int
    run_id: str
    task_id: str | None
    status: str
    started_at_unix: float
    duration_seconds: float
    workspace: str | None = None
    agent: CommandResult | None = None
    graders: list[GraderResult] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _run_command(command: str, cwd: Path, timeout_seconds: int, env: dict[str, str] | None = None) -> CommandResult:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        return CommandResult(
            command=command,
            exit_code=completed.returncode,
            duration_seconds=time.monotonic() - started,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return CommandResult(
            command=command,
            exit_code=None,
            duration_seconds=time.monotonic() - started,
            stdout=stdout,
            stderr=stderr,
            timed_out=True,
        )


def _load_task(task_path: Path) -> dict[str, Any]:
    schema = load_schema()
    issues = validate_file(task_path, schema)
    if issues:
        rendered = "; ".join(issue.render() for issue in issues)
        raise ValueError(rendered)
    with task_path.open(encoding="utf-8") as handle:
        task = yaml.safe_load(handle)
    if not isinstance(task, dict):
        raise ValueError("task document must be an object")
    return task


def _resolve_source(task_path: Path, source: str) -> Path:
    candidate = Path(source)
    if not candidate.is_absolute():
        repo_relative = Path.cwd() / candidate
        task_relative = task_path.parent / candidate
        candidate = repo_relative if repo_relative.exists() else task_relative
    return candidate.resolve()


def _prepare_workspace(task_path: Path, task: dict[str, Any], workspace_root: Path | None) -> Path:
    source = _resolve_source(task_path, task["repository"]["source"])
    if not source.is_dir():
        raise ValueError(f"repository source is not a local directory: {source}")
    root = workspace_root or Path(tempfile.mkdtemp(prefix="feh-run-"))
    root.mkdir(parents=True, exist_ok=True)
    workspace = root / "workspace"
    if workspace.exists():
        shutil.rmtree(workspace)
    shutil.copytree(source, workspace, ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__"))
    return workspace


def _write_result(result: RunResult, output_path: Path | None) -> None:
    if output_path is None:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")


def run_task(
    task_path: Path,
    agent_command: str,
    *,
    output_path: Path | None = None,
    workspace_root: Path | None = None,
) -> RunResult:
    started_at = time.time()
    monotonic_started = time.monotonic()
    result = RunResult(
        schema_version=1,
        run_id=str(uuid.uuid4()),
        task_id=None,
        status="invalid_configuration",
        started_at_unix=started_at,
        duration_seconds=0.0,
    )

    try:
        task = _load_task(task_path)
        result.task_id = task["id"]
        workspace = _prepare_workspace(task_path, task, workspace_root)
        result.workspace = str(workspace)

        max_wall = int(task.get("budgets", {}).get("max_wall_seconds", 3600))
        setup_command = task["repository"].get("setup_command")
        if setup_command:
            setup = _run_command(setup_command, workspace, max_wall)
            if setup.timed_out:
                result.status = "timeout"
                result.error = "setup command timed out"
                return result
            if setup.exit_code != 0:
                result.status = "invalid_configuration"
                result.error = f"setup command failed with exit code {setup.exit_code}: {setup.stderr}"
                return result

        env = os.environ.copy()
        env["FEH_TASK_ID"] = task["id"]
        env["FEH_TASK_PROMPT"] = task["prompt"]
        agent = _run_command(agent_command, workspace, max_wall, env)
        result.agent = agent
        if agent.timed_out:
            result.status = "timeout"
            result.error = "agent command timed out"
            return result
        if agent.exit_code != 0:
            result.status = "agent_failed"
            result.error = f"agent command failed with exit code {agent.exit_code}"
            return result

        for grader in task["graders"]:
            if grader["type"] != "command":
                raise ValueError(f"unsupported grader type in runner MVP: {grader['type']}")
            command_result = _run_command(
                grader["command"],
                workspace,
                int(grader.get("timeout_seconds", max_wall)),
            )
            passed = not command_result.timed_out and command_result.exit_code == 0
            result.graders.append(
                GraderResult(
                    type="command",
                    passed=passed,
                    command_result=command_result,
                    message=None if passed else "command grader failed",
                )
            )

        result.status = "passed" if all(grader.passed for grader in result.graders) else "grader_failed"
        return result
    except (OSError, ValueError, yaml.YAMLError) as exc:
        result.status = "invalid_configuration"
        result.error = str(exc)
        return result
    finally:
        result.duration_seconds = time.monotonic() - monotonic_started
        _write_result(result, output_path)
