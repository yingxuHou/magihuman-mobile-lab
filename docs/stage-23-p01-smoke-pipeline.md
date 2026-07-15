# Stage 23: P01 256p Smoke Pipeline

Date: 2026-07-16

Status: complete for local tooling, not executed on GPU

## Goal

Create a smallest-first GPU execution path for the first real reproduction run.

The full required suite is P01/P03/P04/T01/T02, but the first GPU attempt should run only P01 until the project has a playable 256p base T2V output and valid metrics. Stage 23 adds a P01-only pipeline that reuses the same experiment matrix, runner, metrics parser, result summary, feasibility decision, and final report generator used by the full suite.

## Files Changed

| File | Purpose |
| --- | --- |
| `scripts/run_p01_smoke_pipeline.sh` | Runs source prep, preflight, optional model download, P01 dry-run or execution, result summary, feasibility decision, and final report |
| `tests/test_p01_smoke_pipeline.py` | Checks that the script targets only P01 and keeps the required first-run gates |
| `docs/stage-23-p01-smoke-pipeline.md` | Records this stage |

## GPU Command

On the GPU host, after entering the generated container:

```bash
INSTALL_MAGICOMPILER=1 DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/run_p01_smoke_pipeline.sh
```

If models are already downloaded:

```bash
EXECUTE=1 bash scripts/run_p01_smoke_pipeline.sh
```

The script writes:

- `logs/p01_preflight_<timestamp>.json`
- `outputs/reports/p01_preflight_<timestamp>.md`
- `outputs/reports/p01_smoke_plan_<timestamp>.sh`
- `logs/p01_smoke_execute_<timestamp>.log` when `EXECUTE=1`
- `outputs/reports/p01_experiment_results_<timestamp>.md`
- `outputs/reports/p01_feasibility_decision_<timestamp>.md`
- `outputs/reports/p01_final_report_<timestamp>.md`

## Why This Exists

P01 is the first required evidence gate:

- 256p
- T2V
- base model
- 5 seconds
- no super-resolution
- no reference image

P03, P04, T01, and T02 should wait until P01 produces a playable mp4 and metrics JSON.

## Local Dry-Run Result

Command:

```powershell
PREPARE_SOURCES=0 MIN_DISK_GIB=0 bash scripts/run_p01_smoke_pipeline.sh
```

Result:

```text
P01 command generated.
Local preflight status remains not_ready because this workstation has no nvidia-smi or torchrun.
No inference was executed.
```

## Validation

Commands:

```powershell
python -m unittest tests.test_p01_smoke_pipeline -v
bash -n scripts/run_p01_smoke_pipeline.sh
```

Result:

```text
Ran 2 tests
OK
```

## Next Step

Run the P01 smoke pipeline on the Linux NVIDIA GPU host. If P01 succeeds, package the evidence and then continue to the full required suite.
