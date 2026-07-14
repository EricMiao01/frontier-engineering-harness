# Experiment and Metrics Specification

## Purpose

This specification defines how to measure the causal value of a harness intervention while keeping the coding model, task, repository state, tools, and resource limits comparable.

The benchmark reports two separate outcomes:

1. **Task performance**: whether the agent completed the engineering task well.
2. **Intervention utility**: whether adding context, skills, or workflow improved outcomes enough to justify its extra cost and burden.

A high task score does not prove that an intervention helped. Utility is always measured relative to a declared reference condition.

## Experimental unit

An experimental unit is one independent agent run on one benchmark task under one condition and one random seed.

The primary paired unit is:

```text
(task, model build, toolset, budget, seed)
```

All compared conditions should share that tuple. When a provider does not expose deterministic seeds, runs remain paired by task and replicate index, and this limitation must be reported.

## Required conditions

### Baseline

The coding agent receives only the task prompt and the repository state required to perform the task. No project harness context or benchmark-specific skill is injected.

### Context-only

The agent receives the same task plus approved durable repository context, such as `AGENTS.md`, domain context, ADRs, and applicable specifications. It receives no procedural skill beyond the agent's native behavior.

### Selective-skills

The agent receives the context-only condition and may load only skills selected by the configured router or explicitly declared for the experiment. Detailed skill bodies are loaded on demand.

### Full-workflow

The agent receives the same durable context and is required to follow the complete configured workflow, including all mandatory stages and gates.

Additional competitor conditions are allowed, but the four conditions above form the default ablation set.

## Controlled variables

Every comparison must record and hold constant where technically possible:

- provider and model identifier
- model build, snapshot, or release date
- reasoning or effort setting
- sampling parameters
- system prompt outside the intervention being tested
- repository and base commit
- task prompt and task version
- operating system and container image
- available tools and permissions
- network policy
- dependency cache state
- token, step, wall-clock, and monetary budgets
- human interaction policy
- retry and timeout policy

A run with a materially different controlled variable must not be included in a paired estimate without being identified as a separate experimental block.

## Repeated runs and stochastic variation

### Minimum replication

Development experiments should use at least 3 runs per task-condition pair. Claims intended for publication should target at least 10 runs when cost permits.

### Run order

Conditions should be randomized or counterbalanced within each task to reduce effects from provider load, changing external services, and operator learning.

### Reporting

For every condition, report:

- number of attempted runs
- number of valid runs
- mean
- median
- standard deviation
- interquartile range
- 95% confidence interval

For paired comparisons, report the distribution of per-pair differences. Bootstrap confidence intervals are the default when metric distributions are bounded or non-normal.

A result must not be described as an improvement when the confidence interval for the paired difference includes zero, unless it is explicitly labeled exploratory.

## Task acceptance

A run is **accepted** only when all mandatory deterministic acceptance checks pass and no mandatory reference or human review criterion is failed.

Let:

```text
A_i = 1 if run i is accepted, otherwise 0
```

The task success rate for condition `c` is:

```text
SuccessRate(c) = sum(A_i) / N_c
```

Partial quality metrics remain useful even when `A_i = 0`, but they must not be substituted for acceptance rate.

## Metric families

All normalized quality metrics use the interval `[0, 1]`, where 1 is best.

### Correctness

Correctness measures externally observable task behavior.

Recommended components:

- weighted functional assertions passed
- regression suite result
- hidden acceptance checks
- specification criteria satisfied

For task `t`:

```text
Correctness = sum(weight_j * result_j) / sum(weight_j)
```

where `result_j` is 1 for pass, 0 for fail, or a documented fractional score for a graded criterion.

Deterministic tests take precedence over model-assisted judgments.

### Scope discipline

Scope discipline measures whether the patch remains proportional to the task.

Recommended penalties include:

- unrelated files changed
- forbidden paths changed
- unnecessary public API changes
- unnecessary dependencies
- speculative abstractions
- behavior changes outside acceptance criteria

The default score is:

```text
ScopeDiscipline = max(0, 1 - sum(normalized_penalty_k))
```

Task authors must declare deterministic penalties where possible. A reference patch may guide review, but byte-level similarity to a gold patch must not be treated as the objective.

### Process quality

Process quality is task-specific. A task declares observable checkpoints and whether each is required, optional, unnecessary, or forbidden.

Examples include:

- reproduced the bug before changing code
- inspected the applicable specification
- tested a root-cause hypothesis
- added a regression test
- gathered completion evidence
- avoided unnecessary clarification

For applicable checkpoints:

```text
ProcessQuality = weighted checkpoints satisfied / applicable checkpoint weight
```

A checkpoint that is unnecessary for the task must not increase the score. Performing a forbidden or unnecessary ceremony may reduce scope discipline, efficiency, or human-burden scores.

### Efficiency

Efficiency is reported as raw measurements rather than collapsed into a single universal score:

- input, output, and cached tokens
- model cost
- tool calls
- files opened
- commands executed
- agent turns
- wall-clock duration
- number of retries

The primary aggregate efficiency measure is cost per accepted task:

```text
CPAT(c) = total monetary cost of valid runs in c / number of accepted runs in c
```

If no run is accepted, CPAT is infinite and must not be omitted.

### Human burden

Human burden records intervention demanded from the operator:

- clarification questions
- approval gates
- user corrections
- manual commands
- manual review minutes

When benchmark tasks contain known material uncertainties:

```text
ClarificationPrecision = material questions asked / all questions asked
ClarificationRecall = material uncertainties surfaced / known material uncertainties
```

If no question is asked, precision is undefined rather than zero. If no material uncertainty exists, recall is not applicable.

## Routing metrics

### Skill invocation precision

```text
InvocationPrecision = useful skill invocations / all skill invocations
```

A useful invocation is one marked useful by the task annotation or independently judged to address an applicable failure mode.

### Skill invocation recall

```text
InvocationRecall = useful skill opportunities invoked / all useful skill opportunities
```

The missed-skill rate is:

```text
MissedSkillRate = 1 - InvocationRecall
```

### No-skill accuracy

```text
NoSkillAccuracy = correct direct routes / tasks annotated as direct
```

No-skill accuracy must be reported separately because over-invocation can improve apparent routing recall while increasing ceremony tax.

## Composite quality

A project may define a weighted quality score:

```text
Quality = w_c * Correctness
        + w_s * ScopeDiscipline
        + w_p * ProcessQuality
```

where weights are non-negative and sum to 1.

The default exploratory weights are:

```text
w_c = 0.60
w_s = 0.25
w_p = 0.15
```

Acceptance rate, raw component metrics, and uncertainty intervals must always be reported beside the composite. The composite must never hide a correctness failure.

## Intervention utility

For intervention condition `x` relative to reference condition `r`:

```text
DeltaQuality = mean(Quality_x - Quality_r) on paired runs
DeltaCost = mean(Cost_x - Cost_r)
DeltaLatency = mean(Latency_x - Latency_r)
DeltaHumanBurden = mean(HumanBurden_x - HumanBurden_r)
```

A configurable utility score is:

```text
Utility(x, r) = DeltaQuality
              - lambda_cost * NormalizedDeltaCost
              - lambda_latency * NormalizedDeltaLatency
              - lambda_human * NormalizedDeltaHumanBurden
```

Lambda values and normalization references must be declared before results are inspected. Utility must be accompanied by its component deltas because different teams value cost, latency, and human attention differently.

## Ceremony tax

Ceremony tax measures additional procedure that does not produce sufficient quality gain.

For condition `x` relative to `r`:

```text
CeremonyTax = ExtraCost
            + ExtraLatency
            + ExtraHumanBurden
```

Each component must be normalized using the experiment's declared reference scale.

An intervention is classified as **dominated** when it has non-positive paired quality gain and positive ceremony tax. Dominated interventions should not be recommended for that task category.

## Grader hierarchy

Graders are ordered by evidentiary strength:

1. deterministic runtime checks
2. deterministic static and structural checks
3. reference-based rubric checks
4. blinded human review
5. model-assisted review

Model-assisted grading must not be the sole acceptance mechanism. When used, record the grader model, prompt, sampling settings, and whether the grader was blinded to the experimental condition.

Human and model reviewers should be blinded to condition names whenever practical.

## Invalid runs

A run is invalid, rather than failed, when infrastructure prevents a fair task attempt, for example:

- repository checkout failure
- unavailable required dependency caused by benchmark infrastructure
- provider outage before meaningful agent action
- corrupted trace
- experiment controller violated the declared budget or tool policy

Agent-caused build failures, timeouts, budget exhaustion, and incorrect tool use are task failures, not invalid runs.

All exclusions and reasons must be reported.

## Bias and limitations

Every report must discuss applicable sources of bias:

- benchmark tasks may not represent production repositories
- public tasks may be contaminated in model training data
- authored tasks may encode the harness designers' assumptions
- mutation tasks may overrepresent local syntactic bugs
- hidden tests may under-specify legitimate solutions
- gold patches may bias scope review toward one implementation
- model-assisted graders may prefer verbose or familiar styles
- provider behavior and pricing may change over time
- human intervention policies may differ from real usage
- repeated runs may not be statistically independent
- routing annotations may reflect subjective skill taxonomy choices

Results apply to the tested task distribution, model build, harness version, and budget. Generalization beyond these conditions must be presented as a hypothesis.

## Required experiment report

Every experiment report must include:

- hypothesis and preregistered decision rule
- task set and inclusion criteria
- harness and skill versions
- all controlled variables
- condition definitions
- run counts and exclusions
- acceptance rate
- component metrics
- paired deltas with uncertainty intervals
- cost per accepted task
- routing metrics where applicable
- limitations and observed failure modes
- machine-readable run and trace identifiers
