# Stage 40: GPU Reproduction Workflow

Date: 2026-07-16

## Goal

Reduce the GPU-host reproduction path to one audited command after the Docker container starts.

The workflow must run P01 first, let the P01 acceptance gate decide whether the full suite can proceed, run the full required suite, let the required-suite acceptance gate decide whether quality/cost review can proceed, and then package the small evidence bundle.

## Implementation

- Added `scripts/run_gpu_reproduction_workflow.sh`.
- Updated `backend/gpu_bootstrap.py` so `--download-models --execute` bootstrap plans use the workflow script instead of starting the full suite directly.
- Added `tests/test_gpu_reproduction_workflow.py`.
- Updated `tests/test_gpu_bootstrap.py` for the new execute-mode container command.

## Default Workflow

Inside the GPU container:

```bash
INSTALL_MAGICOMPILER=1 bash scripts/run_gpu_reproduction_workflow.sh
```

Defaults:

- `UPSTREAM_DRIFT_AUDIT=1`
- `PREPARE_SOURCES=1`
- `RUN_P01=1`
- `RUN_FULL=1`
- `PACKAGE_EVIDENCE=1`
- `P01_DOWNLOAD_MODELS=1`
- `FULL_DOWNLOAD_MODELS=1`
- `INCLUDE_OPTIONAL=0`

The script writes `outputs/reports/gpu_reproduction_workflow_<timestamp>.md`.

## Gate Order

1. Upstream drift audit.
2. Locked source preparation.
3. P01 smoke pipeline.
4. P01 acceptance gate inside the P01 pipeline.
5. Required-suite pipeline.
6. Required-suite acceptance gate inside the full pipeline.
7. GPU evidence package.

If any step fails, the workflow summary records the failed step and exits non-zero.

## Validation

Targeted validation passed:

```powershell
python -m unittest tests.test_gpu_reproduction_workflow tests.test_gpu_bootstrap -v
bash -n scripts/run_gpu_reproduction_workflow.sh
python -m backend.gpu_bootstrap --download-models --execute --format markdown
```

The targeted set contains 9 tests.
