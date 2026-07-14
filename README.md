# Frontier Engineering Harness

A lightweight, composable engineering harness for frontier coding agents, paired with a reproducible benchmark that measures whether each context, skill, and workflow intervention earns its cost.

## Principles

- Context before process.
- Verification over ceremony.
- Autonomy within boundaries.
- Use the lightest workflow sufficient for the task.
- Every instruction has a cost.
- Every skill should prove its utility through benchmark evidence.

## Repository layout

```text
harness/       Context, routing, and composable engineering skills
benchmark/     Tasks, graders, runners, traces, and reports
openspec/      Durable behavior specifications and change deltas
docs/adr/      Architectural decisions
```

## Initial research questions

1. Do selective skills outperform a strong model with no added workflow?
2. Which skills improve correctness, scope discipline, and verification?
3. When does a full workflow create ceremony tax?
4. Can skill routing correctly choose no skill?
5. How should utility balance quality, cost, latency, and human burden?

## MVP

The first milestone is a 12-task benchmark across four categories:

- direct changes
- repository exploration
- difficult bugs
- ambiguous features

Each task will be tested under:

- baseline
- context-only
- selective skills
- full workflow
