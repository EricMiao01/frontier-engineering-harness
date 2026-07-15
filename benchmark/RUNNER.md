# Benchmark Runner MVP

The runner connects a validated benchmark task to a configurable local command adapter and deterministic command graders.

## Lifecycle

1. Load and validate the task YAML against `benchmark/task.schema.json`.
2. Resolve `repository.source` to a local directory.
3. Copy the source into an isolated workspace.
4. Run the optional repository setup command.
5. Execute the configured agent command with `FEH_TASK_ID` and `FEH_TASK_PROMPT` in the environment.
6. Execute each command grader in the resulting workspace.
7. Write a machine-readable run result.

## Usage

```bash
feh-run-task path/to/task.yaml \
  --agent-command 'your-agent-command' \
  --output artifacts/run.json
```

The command adapter is intentionally generic. A shell script may invoke a coding agent, a deterministic fixture mutation, or a test double. Vendor-specific Codex and Claude adapters are outside the MVP.

## Statuses

- `passed`: the agent command and every command grader succeeded.
- `agent_failed`: the agent command returned a non-zero exit code.
- `grader_failed`: the agent command succeeded but at least one grader failed.
- `timeout`: setup, agent execution, or grading exceeded its configured timeout.
- `invalid_configuration`: task validation, workspace preparation, setup, or unsupported grader configuration failed.

## Current limitations

- Only local directory repository sources are supported.
- Only `command` graders are executable. Other grader contracts remain valid task metadata but are rejected by this MVP runner.
- The runner records wall-clock duration and command output, but token and tool traces require a future agent adapter.
- Workspace isolation is directory-based rather than container-based.
- Parallel execution and experiment matrix orchestration are not included.
