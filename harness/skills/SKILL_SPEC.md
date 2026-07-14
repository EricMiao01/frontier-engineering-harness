# Skill Metadata and Discovery Specification v1

## Purpose

Define a minimal, vendor-neutral contract for describing, discovering, invoking, and observing engineering skills without requiring one agent runtime.

## Skill package

Each skill is a directory with:

- `skill.yaml`: machine-readable metadata.
- `SKILL.md`: concise executable guidance.
- `references/`: optional details loaded only after selection.
- `tests/`: optional independent tests or examples.

Only `skill.yaml` is required for discovery. The router must not load full skill bodies before selection.

## Metadata fields

Required:

- `id`: stable lowercase identifier using letters, digits, and hyphens.
- `version`: positive integer contract version.
- `name`: short human-readable name.
- `description`: one sentence describing the failure mode or situation addressed.
- `invocation`: one of `model`, `user`, or `both`.
- `triggers`: one or more concise observable task signals.
- `body`: relative path to the skill body.

Optional:

- `anti_triggers`: signals that argue against selection.
- `references`: detailed files available through progressive disclosure.
- `requires`: capabilities or tools required to execute the skill.
- `produces`: observable outputs expected from the skill.
- `tags`: coarse deterministic discovery labels.
- `compatibility`: runtime-specific adapter notes.

Descriptions must state when the skill helps, not advertise general quality. Avoid descriptions such as “use for better coding.”

## Invocation modes

### Model-invoked

The router may select the skill based on task signals. The selection must be logged.

### User-invoked

The skill is activated only by an explicit user command or runtime-specific alias. The router must not silently activate it.

### Both

The skill may be selected automatically or explicitly.

User invocation takes precedence over automatic routing unless it violates a declared capability constraint.

## MVP discovery

The MVP uses deterministic metadata filtering rather than semantic search:

1. Read only skill metadata.
2. Filter by invocation mode and available capabilities.
3. Match declared tags and trigger predicates against the task classification.
4. Evaluate anti-triggers.
5. Return one routing decision.

Semantic search may be evaluated later as a separate intervention. It is not part of v1.

## Routing decisions

Every decision must be exactly one of:

- `direct`: execute without a skill.
- `skill`: invoke one selected skill.
- `compose`: invoke an ordered list of independently testable skills.
- `clarify`: request missing information before execution.

`direct` is a first-class successful routing outcome. The router must not select a skill merely because one exists.

For `skill` and `compose`, the decision records selected skill IDs and versions. For `direct`, the list is empty.

## Progressive disclosure

The runtime loads information in three stages:

1. Metadata for all discoverable skills.
2. `SKILL.md` only for selected skills.
3. Reference files only when the selected body explicitly identifies a need.

Reference loading must be observable so context cost can be measured.

## Independent testability

A skill body must define:

- Preconditions.
- Expected behavior changes.
- Completion or exit criteria.
- Observable outputs.

A skill must not require another skill unless the dependency is declared in metadata. Compositions belong in routing or workflow definitions, not hidden inside unrelated skill bodies.

## Runtime mapping

The contract maps to runtime conventions through adapters:

- Codex-like runtimes can expose metadata through repository instructions or installed skill registries.
- Claude Code-like runtimes can map user invocation to slash commands and model invocation to descriptions or routing instructions.

Runtime adapters may rename fields externally but must preserve the canonical skill ID, version, invocation mode, and trace semantics.

## Benchmark observability

Each run must record:

- Available skill IDs and versions.
- Routing decision and reason codes.
- Selected skills and order.
- Whether selection was user- or model-initiated.
- Skill body and reference files loaded.
- Timestamps or sequence indices for selection and loading.
- Router overrides, failures, and fallbacks.

These fields support invocation precision, missed-skill rate, no-skill accuracy, context cost, and ceremony-tax analysis.
