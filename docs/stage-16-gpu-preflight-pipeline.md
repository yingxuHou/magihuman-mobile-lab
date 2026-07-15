# Stage 16: GPU Preflight And Reproduction Pipeline

Date: 2026-07-16

Status: complete for local tooling

## Goal

Reduce the remaining cloud GPU work to one auditable command sequence.

Before this stage, the repository had separate scripts for:

- cloud environment checks
- model download
- required experiment suite execution
- experiment result summary
- mobile feasibility decision

Stage 16 adds a structured preflight checker and a single pipeline script that ties those steps together.

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/gpu_preflight.py` | Produces machine-readable GPU host readiness checks |
| `tests/test_gpu_preflight.py` | Tests command checks, path checks, model requirements, and Markdown rendering |
| `scripts/gpu_reproduction_pipeline.sh` | Runs preflight, optional model download, experiment suite, result summary, and feasibility decision |
| `docs/cloud-gpu-runbook.md` | Documents the pipeline-first GPU workflow |

## Current Local Preflight

Command:

```powershell
python -m backend.gpu_preflight --mode container --require-models --min-disk-gib 0 --format markdown
```

Current local result:

```text
Status: not_ready
Missing required execution items include nvidia-smi, torchrun, model root, and model directories.
```

This confirms the current Windows workstation still cannot perform the actual inference run.

## GPU Host Pipeline

Dry run on a prepared Linux GPU host:

```bash
bash scripts/gpu_reproduction_pipeline.sh
```

Execute required experiments:

```bash
EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

Download models first, then execute:

```bash
DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

Include optional cases:

```bash
INCLUDE_OPTIONAL=1 EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

With a completed quality review:

```bash
QUALITY_REVIEW=docs/quality-review.json EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

## Pipeline Outputs

The pipeline writes:

- `logs/gpu_preflight_<timestamp>.json`
- `outputs/reports/gpu_preflight_<timestamp>.md`
- `logs/experiment_suite_<timestamp>.log` or `logs/experiment_suite_dryrun_<timestamp>.sh`
- `outputs/reports/experiment_results_<timestamp>.md`
- `outputs/reports/feasibility_decision_<timestamp>.md`

Large runtime outputs remain ignored by Git.

## Validation

Commands:

```powershell
python -m unittest tests.test_gpu_preflight -v
python -m backend.gpu_preflight --mode host --min-disk-gib 0 --format json
```

Result:

```text
Ran 5 tests
OK
```

## Next Step

Run this on the GPU host:

```bash
DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

Then review the generated reports and commit the stage results.
