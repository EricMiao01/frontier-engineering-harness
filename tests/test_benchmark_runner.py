from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

from benchmark.runner.runner import run_task


def _write_task(
    tmp_path: Path,
    *,
    grader: str,
    max_wall_seconds: int = 5,
    repository_source: str | None = None,
    base_commit: str = "fixture-v1",
) -> Path:
    if repository_source is None:
        source = tmp_path / "fixture"
        source.mkdir()
        (source / "value.txt").write_text("healthy\n", encoding="utf-8")
        repository_source = str(source)
    task = {
        "id": "runner-test",
        "version": 1,
        "source": "authored",
        "category": "direct_change",
        "difficulty": "easy",
        "repository": {"source": repository_source, "base_commit": base_commit},
        "prompt": "Make the fixture pass its grader.",
        "acceptance": ["The command grader passes."],
        "routing_expectations": {"mode": "direct", "useful_skills": []},
        "graders": [{"type": "command", "command": grader}],
        "budgets": {"max_steps": 10, "max_tokens": 1000, "max_wall_seconds": max_wall_seconds},
    }
    task_path = tmp_path / "task.yaml"
    task_path.write_text(yaml.safe_dump(task, sort_keys=False), encoding="utf-8")
    return task_path


def _create_git_repository(tmp_path: Path) -> tuple[Path, str]:
    repository = tmp_path / "source-repo"
    repository.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=repository, check=True)
    subprocess.run(["git", "config", "user.email", "ci@example.com"], cwd=repository, check=True)
    subprocess.run(["git", "config", "user.name", "CI"], cwd=repository, check=True)
    (repository / "value.txt").write_text("committed\n", encoding="utf-8")
    subprocess.run(["git", "add", "value.txt"], cwd=repository, check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "fixture"], cwd=repository, check=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    return repository, commit


def test_successful_run_writes_result(tmp_path: Path) -> None:
    task_path = _write_task(
        tmp_path,
        grader=f'{sys.executable} -c "from pathlib import Path; assert Path(\'value.txt\').read_text() == \'changed\\n\'"',
    )
    output = tmp_path / "artifacts" / "run.json"
    command = f'{sys.executable} -c "from pathlib import Path; Path(\'value.txt\').write_text(\'changed\\n\')"'

    result = run_task(task_path, command, output_path=output, workspace_root=tmp_path / "run")

    assert result.status == "passed"
    assert result.agent is not None and result.agent.exit_code == 0
    assert result.graders[0].passed is True
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "passed"


def test_git_source_checks_out_exact_base_commit(tmp_path: Path) -> None:
    repository, commit = _create_git_repository(tmp_path)
    task_path = _write_task(
        tmp_path,
        repository_source=repository.as_uri(),
        base_commit=commit,
        grader=f'{sys.executable} -c "from pathlib import Path; assert Path(\'value.txt\').read_text() == \'committed\\n\'"',
    )

    result = run_task(
        task_path,
        f'{sys.executable} -c "pass"',
        workspace_root=tmp_path / "run",
    )

    assert result.status == "passed"
    assert result.workspace is not None
    workspace = Path(result.workspace)
    checked_out = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=workspace,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    assert checked_out == commit


def test_missing_git_commit_is_invalid_configuration(tmp_path: Path) -> None:
    repository, _ = _create_git_repository(tmp_path)
    task_path = _write_task(
        tmp_path,
        repository_source=repository.as_uri(),
        base_commit="0" * 40,
        grader=f'{sys.executable} -c "pass"',
    )

    result = run_task(task_path, f'{sys.executable} -c "pass"', workspace_root=tmp_path / "run")

    assert result.status == "invalid_configuration"
    assert result.error is not None
    assert "git checkout failed" in result.error
    assert "0000000000000000000000000000000000000000" in result.error


def test_agent_failure_is_distinct(tmp_path: Path) -> None:
    task_path = _write_task(tmp_path, grader=f'{sys.executable} -c "pass"')
    result = run_task(task_path, f'{sys.executable} -c "raise SystemExit(7)"')
    assert result.status == "agent_failed"
    assert result.agent is not None and result.agent.exit_code == 7


def test_grader_failure_is_distinct(tmp_path: Path) -> None:
    task_path = _write_task(tmp_path, grader=f'{sys.executable} -c "raise SystemExit(3)"')
    result = run_task(task_path, f'{sys.executable} -c "pass"')
    assert result.status == "grader_failed"
    assert result.graders[0].command_result is not None
    assert result.graders[0].command_result.exit_code == 3


def test_timeout_is_distinct(tmp_path: Path) -> None:
    task_path = _write_task(tmp_path, grader=f'{sys.executable} -c "pass"', max_wall_seconds=1)
    result = run_task(task_path, f'{sys.executable} -c "import time; time.sleep(2)"')
    assert result.status == "timeout"
    assert result.agent is not None and result.agent.timed_out is True


def test_invalid_task_is_distinct(tmp_path: Path) -> None:
    task_path = tmp_path / "invalid.yaml"
    task_path.write_text("id: invalid\n", encoding="utf-8")
    result = run_task(task_path, f'{sys.executable} -c "pass"')
    assert result.status == "invalid_configuration"
    assert result.error
