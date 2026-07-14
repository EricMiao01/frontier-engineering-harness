# ADR 0002: Separate Task Performance from Intervention Utility

## Status

Proposed

## Context

A coding agent can solve a task while a harness intervention adds no value, and an intervention can improve one quality dimension while adding unacceptable cost, latency, or human burden. Reporting only pass rate cannot distinguish these cases.

## Decision

The benchmark will report task performance and intervention utility separately.

Task performance includes acceptance rate, correctness, scope discipline, and task-specific process quality.

Intervention utility is a paired comparison against a declared reference condition. It reports quality gain alongside added cost, latency, and human burden. Composite utility scores are allowed only when their weights and normalization rules are declared before inspecting results.

Raw component metrics and uncertainty intervals remain mandatory even when a composite is used.

## Consequences

- A successful task does not automatically count as evidence for a skill or workflow.
- Interventions with non-positive quality gain and positive ceremony tax can be identified as dominated.
- Different teams may apply different utility weights without changing the underlying experimental observations.
- Experiment reports require paired conditions and repeated runs where feasible.
