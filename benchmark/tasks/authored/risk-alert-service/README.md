# Risk Alert Service Authored Tasks

These tasks reuse the healthy repository in `benchmark/fixtures/risk-alert-service` without storing broken fixture variants.

## Task set

| Task | Category | Intended routing | Primary signal |
| --- | --- | --- | --- |
| `risk-alert-large-amount-threshold` | direct change | direct | no-skill accuracy and scope discipline |
| `risk-alert-notification-path` | repository exploration | explore | repository navigation and architecture comprehension |
| `risk-alert-duplicate-alert-id` | difficult bug | diagnose + verify | reproduction, root cause, and regression testing |
| `risk-alert-severe-case-notification` | ambiguous feature | clarify | restraint and clarification under underspecification |

## Reset model

The runner copies the healthy fixture into a temporary workspace for every run. A task may then apply a deterministic `repository.setup_command` inside that copy. The source fixture is never mutated.

The duplicate-alert task injects its bug by replacing the alert ID input only in the temporary workspace. Re-running the task starts from the healthy source again.

## Grading boundaries

Direct change and difficult bug use behavioral command graders plus the fixture test suite.

Repository exploration writes `INVESTIGATION.md`; its MVP grader checks required architectural concepts. This provides deterministic coverage but cannot fully judge semantic quality, so later experiments should add blind review or a reference-based grader.

The ambiguous feature is currently a routing-trace task. The command grader only confirms the healthy repository remains valid. Correct clarification behavior cannot be scored by the runner until an interaction-aware grader and trace ingestion are implemented.

## Local validation

```bash
python -m benchmark.validate_tasks benchmark/tasks/authored/risk-alert-service
python -m pytest -q
```
