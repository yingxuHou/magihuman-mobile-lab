# Stage 11: Result Aggregation

Date: 2026-07-15

Status: complete for local aggregation logic

## Goal

Prepare the reporting layer that turns GPU run metrics into a readable feasibility table.

The project needs a final decision based on evidence. This stage makes missing evidence explicit and gives us a repeatable way to summarize runs after the GPU host executes the experiment matrix.

## Files Added

| File | Purpose |
| --- | --- |
| `backend/experiment_results.py` | Aggregates metrics JSON files by experiment case |
| `tests/test_experiment_results.py` | Tests missing/measured summary behavior |
| `scripts/summarize_experiment_results.ps1` | Windows summary launcher |
| `scripts/summarize_experiment_results.sh` | Linux summary launcher |

## Current Behavior

The aggregator:

- reads the experiment matrix
- looks for latest `logs/{case_id}_*_metrics.json`
- marks cases as `missing_metrics`, `incomplete_metrics`, or `measured`
- produces a Markdown table
- returns `insufficient_runtime_evidence` until required cases have metrics

Required cases currently include:

- `P01`: 256p base smoke test
- `P03`: 540p SR
- `P04`: 1080p SR
- `T01`: Mandarin TI2V
- `T02`: English TI2V

## Example Command

```powershell
python -m backend.experiment_results --log-dir logs --format markdown
```

Or:

```powershell
.\scripts\summarize_experiment_results.ps1 -LogDir logs -Format markdown
```

## Validation

Command:

```powershell
python -m unittest discover -s tests -v
```

Result:

```text
Ran 27 tests
OK
```

## Next Step

After each GPU run:

1. keep the generated metrics JSON under `logs/`
2. run the result summarizer
3. paste the table into `docs/reproduction-log.md`
4. update `docs/mobile-feasibility.md`
5. push the report to GitHub
