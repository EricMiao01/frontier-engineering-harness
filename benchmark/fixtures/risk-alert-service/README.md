# Risk Alert Service Fixture

A deterministic, dependency-light repository fixture for coding-agent benchmark tasks.

## Stack

- Python 3.11+
- Standard-library domain implementation
- pytest for tests
- In-memory repositories and recording ports

The fixture avoids databases, network calls, clocks in assertions, and paid services. Stable IDs are derived from inputs so every run is reproducible.

## Architecture boundaries

- `models.py`: domain entities only
- `rules.py`: pure risk-rule evaluation
- `repositories.py`: persistence adapters
- `ports.py`: notification and audit boundaries
- `services.py`: orchestration and domain workflows

Rules must not write repositories. Repositories must not send notifications. Services may coordinate these boundaries.

## Run

```bash
python -m pytest -q
```

## Reset strategy

The healthy fixture is the canonical base. Each benchmark task should be created as a patch or commit derived from this base and reset by checking out its recorded `base_commit`.
