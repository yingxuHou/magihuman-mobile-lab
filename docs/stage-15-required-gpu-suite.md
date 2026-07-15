# Stage 15: Required GPU Experiment Suite

Date: 2026-07-16

Status: complete for local orchestration tooling

## Goal

Prepare the exact required GPU run sequence for the mobile feasibility decision.

Stage 14 made the decision repeatable and showed that the current missing runtime evidence is:

- P01
- P03
- P04
- T01
- T02

Stage 15 turns those required cases into one ordered suite that can be dry-run locally and executed on a Linux NVIDIA GPU host.

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/experiment_suite.py` | Plans or executes the required GPU experiment suite |
| `tests/test_experiment_suite.py` | Tests required order, dependency blocking, measured-case skipping, and renderers |
| `scripts/run_experiment_suite.ps1` | Windows launcher for planning |
| `scripts/run_experiment_suite.sh` | Linux launcher for planning or execution |

## Required Suite

Default order:

| Case | Purpose | Dependency |
| --- | --- | --- |
| P01 | 256p base T2V smoke test | none |
| P03 | 540p SR T2V | P01 |
| P04 | 1080p SR T2V | P01, P03 |
| T01 | Mandarin TI2V | P01 |
| T02 | English TI2V | P01 |

Optional cases are available with `--include-optional`:

- P02
- T03
- T04

## Local Dry Run

Command:

```powershell
python -m backend.experiment_suite --log-dir logs --format markdown
```

Current local output:

```text
P01 run missing_metrics
P03 run missing_metrics
P04 run missing_metrics
T01 run missing_metrics
T02 run missing_metrics
```

This confirms the suite is ready to run, but the current Windows workstation still cannot execute the model because it has no NVIDIA GPU/CUDA/Docker/Conda environment.

## GPU Host Execution

On a Linux NVIDIA GPU host after source and model preparation:

```bash
bash scripts/run_experiment_suite.sh --execute
```

Useful variants:

```bash
FORMAT=markdown bash scripts/run_experiment_suite.sh
bash scripts/run_experiment_suite.sh --include-optional
bash scripts/run_experiment_suite.sh --rerun --execute
```

The suite skips cases that already have valid metrics unless `--rerun` is used.

## Validation

Command:

```powershell
python -m unittest tests.test_experiment_suite -v
```

Result:

```text
Ran 5 tests
OK
```

## Next Step

Run the suite on the GPU host, then summarize and decide:

```bash
bash scripts/run_experiment_suite.sh --execute
python -m backend.experiment_results --log-dir logs --format markdown
python -m backend.feasibility_decision --log-dir logs --format markdown
```
