# Benchmark Task Specification v1

A task file is a vendor-neutral YAML contract describing the repository state, user request, expected routing, grading, and execution budget for one benchmark case.

## Validation

```bash
python -m benchmark.validate_tasks benchmark/examples/valid
feh-validate-tasks benchmark/examples/valid
```

The command accepts files or directories. It exits with `0` when all task files are valid, `1` for schema validation failures, and `2` when no YAML task files are found. Errors include the file, exact field path, and reason.

## Required top-level fields

- `id`: stable kebab-case identifier.
- `version`: currently `1`.
- `source`: `authored`, `mutation`, `historical_pr`, or `public_import`.
- `category`: the engineering behavior being evaluated.
- `difficulty`: `easy`, `medium`, or `hard`.
- `repository`: reproducible source and base commit.
- `prompt`: the user-facing task request.
- `acceptance`: observable completion criteria.
- `routing_expectations`: whether direct execution or selected skills are expected.
- `graders`: deterministic or reference-based checks.
- `budgets`: step and token limits.

## Routing and explicit no-skill tasks

`routing_expectations.mode: direct` means the correct routing decision is to use no skill. In this mode `useful_skills` must be empty. This makes over-invocation measurable rather than treating every task as a tool-selection problem.

`routing_expectations.mode: selective_skills` requires at least one `useful_skills` entry. `unnecessary_skills` records tempting but wasteful interventions.

## Categories

- `direct_change`
- `repository_exploration`
- `difficult_bug`
- `ambiguous_feature`
- `architecture_boundary`
- `external_research`
- `long_horizon`

## Process expectations

Optional booleans describe task-specific process evidence, not a universal workflow: reproduction, clarification, specification, regression testing, and root-cause identification.

## Graders

Version 1 supports:

- `command`: execute a deterministic command.
- `diff_scope`: constrain allowed paths.
- `architecture`: evaluate a named repository-specific rule.

## Extensibility

Unknown top-level fields are rejected to catch mistakes. Experiment-specific annotations belong under `metadata`, which deliberately permits additional fields. The schema does not mention Codex, Claude Code, or any model vendor.
