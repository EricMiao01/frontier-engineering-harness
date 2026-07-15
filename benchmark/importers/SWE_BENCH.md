# SWE-bench Importer

The importer converts versioned SWE-bench JSON or JSONL records into this repository's canonical task YAML.

## Supported input

Each record must contain:

- `instance_id`
- `repo`
- `base_commit`
- `problem_statement`

Optional provenance fields such as `version`, `created_at`, and `environment_setup_commit` are retained in task metadata. Gold `patch` and `test_patch` fields are deliberately ignored and never written to agent-visible manifests.

## Usage

```bash
feh-import-swe-bench records.jsonl benchmark/tasks/imported/swe-bench \
  --dataset-name princeton-nlp/SWE-bench_Verified \
  --instance-id sympy__sympy-20590 \
  --limit 5
```

Output is sorted by `instance_id` and serialized deterministically so the same input produces byte-stable YAML.

## Evaluation boundary

Imported manifests establish:

- the exact Git repository source;
- the exact pre-solution `base_commit`;
- the issue text presented to the agent;
- provenance required to reconnect the task to official evaluation.

They do **not** reproduce official SWE-bench grading. Official evaluation uses Docker images and test metadata such as `FAIL_TO_PASS` and `PASS_TO_PASS`. Until a dedicated adapter exists, imported manifests use a non-executable `diff_scope` grader placeholder and set `metadata.official_evaluation_required: true`.

This boundary prevents the repository from claiming equivalence with SWE-bench based only on repository checkout and prompt mapping.

## Dataset snapshots

Do not fetch a mutable dataset during CI. Commit a reviewed, versioned source snapshot or record its immutable dataset revision before generating checked-in task manifests. CI tests use synthetic records solely to verify importer behavior.
