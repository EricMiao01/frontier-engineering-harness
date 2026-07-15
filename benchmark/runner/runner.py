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
from typing import Any, Sequence

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


def _run_process(args: Sequence[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(args),
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise ValueError(f"unable to execute {args[0]!r}: {exc}") from exc


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


def _resolve_local_source(task_path: Path, source: str) -> Path:
    candidate = Path(source)
    if not candidate.is_absolute():
        repo_relative = Path.cwd() / candidate
        task_relative = task_path.parent / candidate
        candidate = repo_relative if repo_relative.exists() else task_relative
    return candidate.resolve()


def _is_git_source(source: str) -> bool:
    return source.startswith(("https://", "http://", "ssh://", "git://", "file://", "git@")) or source.endswith(".git")


def _copy_local_workspace(task_path: Path, source: str, workspace: Path) -> None:
    resolved = _resolve_local_source(task_path, source)
    if not resolved.is_dir():
        raise ValueError(f"repository source is not a local directory: {resolved}")
    shutil.copytree(resolved, workspace, ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__"))


def _clone_git_workspace(source: str, base_commit: str, workspace: Path) -> None:
    clone = _run_process(["git", "clone", "--no-checkout", "--quiet", source, str(workspace)])
    if clone.returncode != 0:
        detail = clone.stderr.strip() or clone.stdout.strip() or "unknown git clone error"
        raise ValueError(f"git clone failed for {source!r}: {detail}")

    checkout = _run_process(["git", "checkout", "--detach", "--quiet", base_commit], cwd=workspace)
    if checkout.returncode != 0:
        detail = checkout.stderr.strip() or checkout.stdout.strip() or "unknown git checkout error"
        raise ValueError(f"git checkout failed for base_commit {base_commit!r}: {detail}")

    head = _run_process(["git", "rev-parse", "HEAD"], cwd=workspace)
    requested = _run_process(["git", "rev-parse", f"{base_commit}^{{commit}}"], cwd=workspace)
    if head.returncode != 0 or requested.returncode != 0:
        raise ValueError(f"unable to verify checked-out base_commit {base_commit!r}")
    if head.stdout.strip() != requested.stdout.strip():
        raise ValueError(
            f"checked-out commit {head.stdout.strip()!r} does not match requested base_commit {requested.stdout.strip()!r}"
        )


def _prepare_workspace(task_path: Path, task: dict[str, Any], workspace_root: Path | None) -> Path:
    repository = task["repository"]
    source = repository["source"]
    base_commit = repository["base_commit"]
    root = workspace_root or Path(tempfile.mkdtemp(prefix="feh-run-"))
    root.mkdir(parents=True, exist_ok=True)
    workspace = root / "workspace"
    if workspace.exists():
        shutil.rmtree(workspace)

    if _is_git_source(source):
        _clone_git_workspace(source, base_commit, workspace)
    else:
        _copy_local_workspace(task_path, source, workspace)
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
