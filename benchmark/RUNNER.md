# Benchmark Runner MVP

The runner connects a validated benchmark task to a configurable local command adapter and deterministic command graders.

## Lifecycle

1. Load and validate the task YAML against `benchmark/task.schema.json`.
2. Prepare an isolated workspace from `repository.source`:
   - copy an existing local directory, or
   - clone a Git source and check out `repository.base_commit` in detached HEAD state.
3. Run the optional repository setup command.
4. Execute the configured agent command with `FEH_TASK_ID` and `FEH_TASK_PROMPT` in the environment.
5. Execute each command grader in the resulting workspace.
6. Write a machine-readable run result.

## Repository sources

An existing local directory keeps the original MVP behavior and is copied without `.git`, `.pytest_cache`, or `__pycache__` directories.

Git preparation is selected for sources beginning with `https://`, `http://`, `ssh://`, `git://`, `file://`, or `git@`, and for sources ending in `.git`. The runner performs:

```text
git clone --no-checkout <source> <workspace>
git checkout --detach <base_commit>
git rev-parse verification
```

`base_commit` must resolve in the cloned repository. Every run receives a fresh clone; mutable worktrees are not reused.

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
- `invalid_configuration`: task validation, clone/checkout, workspace preparation, setup, or unsupported grader configuration failed.

## Security and operational boundaries

Repository sources and setup commands are trusted benchmark configuration. Cloning and executing arbitrary repositories can run untrusted code during setup, agent execution, or grading. Use an isolated CI runner or container for externally sourced tasks.

## Current limitations

- Git authentication is delegated to the local Git installation; the runner has no GitHub-specific credential handling.
- Submodules, Git LFS, sparse checkout, shallow clone optimization, and repository caching are not supported.
- Only `command` graders are executable. Other grader contracts remain valid task metadata but are rejected by this MVP runner.
- The runner records wall-clock duration and command output, but token and tool traces require a future agent adapter.
- Workspace isolation is filesystem-based rather than container-based.
- Parallel execution and experiment matrix orchestration are not included.
