from pathlib import Path

from benchmark.validate_tasks import load_schema, main, validate_file

ROOT = Path(__file__).parents[1]
VALID = ROOT / "benchmark" / "examples" / "valid"
INVALID = ROOT / "benchmark" / "examples" / "invalid"


def test_valid_examples_pass_schema() -> None:
    schema = load_schema(ROOT / "benchmark" / "task.schema.json")
    for path in VALID.glob("*.yaml"):
        assert validate_file(path, schema) == []


def test_invalid_examples_report_field_paths() -> None:
    schema = load_schema(ROOT / "benchmark" / "task.schema.json")
    missing = validate_file(INVALID / "missing-required-field.yaml", schema)
    routing = validate_file(INVALID / "direct-with-skill.yaml", schema)

    assert any("budgets" in issue.message for issue in missing)
    assert any(issue.field == "routing_expectations.useful_skills" for issue in routing)


def test_cli_validates_directory(capsys) -> None:
    assert main([str(VALID)]) == 0
    assert "validated 2 task file(s)" in capsys.readouterr().out


def test_cli_returns_failure_for_invalid_directory(capsys) -> None:
    assert main([str(INVALID)]) == 1
    captured = capsys.readouterr()
    assert "routing_expectations.useful_skills" in captured.err
    assert "FAILED" in captured.err
