# Agent Instructions

## Mission

Build a lightweight engineering harness and benchmark for frontier coding agents.

## Working principles

- Prefer small, reviewable changes.
- Do not add workflow steps without a measurable failure mode.
- Keep skills composable and independently testable.
- Avoid duplicating guidance across AGENTS.md, skills, OpenSpec, and ADRs.
- Treat benchmark design as a first-class product concern.
- Never claim an intervention helps without comparative evidence.

## Definition of done

A change is complete only when:

1. Its intended behavior is documented.
2. Relevant automated checks pass.
3. The diff is scoped to the stated goal.
4. Any new harness intervention has a proposed benchmark evaluation.
