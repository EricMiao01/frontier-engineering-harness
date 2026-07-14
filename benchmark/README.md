# Benchmark

## Objective

Measure the causal value of context, skills, routing, and workflows while holding the model, task, tools, repository state, and budget constant.

The benchmark separates:

- **task performance**: whether the engineering task was completed well
- **intervention utility**: whether added context, skills, or workflow earned their cost

See [`EXPERIMENT_SPEC.md`](EXPERIMENT_SPEC.md) for experimental controls, formulas, repeated-run reporting, grader hierarchy, ceremony tax, and bias requirements.

## Initial conditions

- baseline
- context-only
- selective-skills
- full-workflow

## Metric families

- correctness
- scope discipline
- process quality
- efficiency
- human burden
- skill invocation precision
- missed-skill rate
- no-skill accuracy
- cost per accepted task
- intervention utility
- ceremony tax

## Task sources

- authored trap tasks
- controlled mutations
- historical open-source pull requests
- selected public benchmark tasks

## Examples

- [`examples/experiment-mvp.yaml`](examples/experiment-mvp.yaml): a machine-readable example of the default four-condition ablation experiment
