from __future__ import annotations

from pathlib import Path

import yaml

from benchmark.runner.runner import run_task
from benchmark.validate_tasks import discover_task_files, load_schema, validate_file

ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = ROOT / "benchmark" / "tasks" / "authored" / "risk-alert-service"
FIXTURE = ROOT / "benchmark" / "fixtures" / "risk-alert-service"


def test_all_authored_tasks_validate() -> None:
    task_files = discover_task_files([TASK_DIR])
    assert {path.name for path in task_files} == {
        "ambiguous-feature.yaml",
        "difficult-bug.yaml",
        "direct-change.yaml",
        "repository-exploration.yaml",
    }

    schema = load_schema()
    issues = [issue for path in task_files for issue in validate_file(path, schema)]
    assert issues == []


def test_direct_change_runs_end_to_end(tmp_path: Path) -> None:
    task_path = TASK_DIR / "direct-change.yaml"
    agent_command = """python - <<'PY'
from pathlib import Path
path = Path('risk_alert_service/rules.py')
text = path.read_text(encoding='utf-8')
text = text.replace('threshold: int = 10_000', 'threshold: int = 15_000', 1)
path.write_text(text, encoding='utf-8')
PY"""

    result = run_task(
        task_path,
        agent_command,
        output_path=tmp_path / "run.json",
        workspace_root=tmp_path / "run",
    )

    assert result.status == "passed"
    assert all(grader.passed for grader in result.graders)
    assert (tmp_path / "run.json").exists()
    assert "threshold: int = 10_000" in (
        FIXTURE / "risk_alert_service" / "rules.py"
    ).read_text(encoding="utf-8")


def test_difficult_bug_setup_only_mutates_workspace(tmp_path: Path) -> None:
    source_path = FIXTURE / "risk_alert_service" / "services.py"
    healthy = source_path.read_text(encoding="utf-8")
    assert 'stable_id("alert", transaction.id)' in healthy

    result = run_task(
        TASK_DIR / "difficult-bug.yaml",
        "true",
        workspace_root=tmp_path / "run",
    )

    assert result.status == "grader_failed"
    workspace_text = (Path(result.workspace) / "risk_alert_service" / "services.py").read_text(
        encoding="utf-8"
    )
    assert 'stable_id("alert", str(transaction.amount))' in workspace_text
    assert source_path.read_text(encoding="utf-8") == healthy


def test_ambiguous_task_documents_interaction_grading_limit() -> None:
    task = yaml.safe_load((TASK_DIR / "ambiguous-feature.yaml").read_text(encoding="utf-8"))
    assert task["process_expectations"]["clarification_required"] is True
    assert task["metadata"]["expected_routing_decision"] == "clarify"
    assert "cannot grade interactive clarification" in task["metadata"]["grading_limitation"]
