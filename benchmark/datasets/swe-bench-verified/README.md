# SWE-bench Verified subset

This directory defines the reviewed instance selection used to materialize the first external benchmark subset.

## Why the records are not copied manually

SWE-bench records must be tied to an immutable dataset revision. The materializer resolves a requested Hugging Face revision to a commit SHA, loads the selected instances from that SHA, generates canonical task manifests, and records `snapshot.json` provenance.

Gold `patch` and `test_patch` fields are ignored by the importer and are not included in generated artifacts.

## Manual workflow

Run **Materialize SWE-bench subset** from GitHub Actions and provide an explicit dataset revision, tag, or commit SHA. The workflow uploads an artifact containing:

- generated task YAML files;
- `snapshot.json` with the resolved dataset revision and selected instance IDs.

The workflow does not commit generated files automatically. Review the artifact before checking manifests into `benchmark/tasks/imported/swe-bench/`.

## Initial selection

The initial selection contains three real SWE-bench Verified instance IDs referenced by the official SWE-bench project. It is intentionally small so repository checkout, prompt mapping, and provenance can be reviewed before increasing task volume.

## Evaluation boundary

These manifests establish reproducible repository state and issue prompts. Official pass/fail grading still requires the SWE-bench Docker evaluation harness and is a separate adapter milestone.
