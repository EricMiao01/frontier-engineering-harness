# ADR 0001: Separate Harness and Benchmark

## Status

Accepted

## Context

A skill library without evaluation can accumulate unproven instructions and workflows. A benchmark without a concrete harness has no intervention model to study.

## Decision

The project will develop two equal, connected products:

1. A lightweight engineering harness.
2. A reproducible benchmark for measuring harness interventions.

Every substantial harness feature should identify the benchmark tasks and metrics that can validate it.

## Consequences

- Benchmark instrumentation is designed from the beginning.
- Skills may be removed when they fail to show net utility.
- The project does not optimize only for task pass rate; efficiency and human burden also matter.
