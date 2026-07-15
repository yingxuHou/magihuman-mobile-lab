# Stage 25: Model Checkpoint Footprint Audit

Date: 2026-07-16

Status: complete for local tooling, waiting for GPU-host downloads

## Goal

Prevent GPU inference from starting with incomplete checkpoint downloads.

Before this stage, preflight only checked whether model directories existed. That is too weak for this project because Hugging Face downloads can be interrupted, gated repositories can silently fail, and empty directories would still pass a directory-only check. Stage 25 adds a checkpoint footprint audit that checks required model groups and minimum expected sizes.

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/model_audit.py` | Audits downloaded checkpoint groups by profile, path, and minimum footprint |
| `tests/test_model_audit.py` | Covers missing, too-small, ready, required-suite, and Markdown states |
| `scripts/model_audit.sh` | Linux launcher |
| `scripts/model_audit.ps1` | Windows launcher |
| `scripts/run_p01_smoke_pipeline.sh` | Runs P01 checkpoint audit before execution and after model download |
| `scripts/gpu_reproduction_pipeline.sh` | Runs required-suite checkpoint audit before execution and after model download |

## Audit Profiles

| Profile | Required groups | Expected footprint |
| --- | --- | ---: |
| `p01` | `base`, `turbo_vae`, `t5gemma`, `stable_audio`, `wan_vae` | 114.64 GiB |
| `required_suite` | `base`, `turbo_vae`, `540p_sr`, `1080p_sr`, `t5gemma`, `stable_audio`, `wan_vae` | 228.62 GiB |
| `complete` | `base`, `turbo_vae`, `distill`, `540p_sr`, `1080p_sr`, `t5gemma`, `stable_audio`, `wan_vae` | 285.61 GiB |

Minimum thresholds are slightly below the expected footprints to tolerate filesystem and GiB/GB reporting differences while still catching missing or obviously partial downloads.

## Commands

Audit P01 models:

```bash
python -m backend.model_audit --model-root models --profile p01 --format markdown
```

Audit the required final-decision suite:

```bash
python -m backend.model_audit --model-root models --profile required_suite --format markdown
```

Fail fast in GPU execution mode:

```bash
python -m backend.model_audit --model-root models --profile p01 --strict
```

## Pipeline Impact

`scripts/run_p01_smoke_pipeline.sh` now writes:

- `logs/p01_model_audit_<timestamp>.json`
- `outputs/reports/p01_model_audit_<timestamp>.md`

`scripts/gpu_reproduction_pipeline.sh` now writes:

- `logs/model_audit_<timestamp>.json`
- `outputs/reports/model_audit_<timestamp>.md`

When `DOWNLOAD_MODELS=1`, the audit runs in report-only mode before download and strict mode after download. When `EXECUTE=1` is used without `DOWNLOAD_MODELS=1`, the initial audit is strict because checkpoint groups are expected to already exist.

## Local Dry-Run Result

Command:

```powershell
python -m backend.model_audit --model-root models --profile p01 --format markdown
```

Current local result:

```text
Status: not_ready
Expected footprint: 114.64 GiB
Found footprint: 0.0000 GiB
```

This is expected on the current workstation because model weights are intentionally not downloaded locally.

## Validation

Commands:

```powershell
python -m unittest tests.test_model_audit -v
PREPARE_SOURCES=0 MIN_DISK_GIB=0 bash scripts/run_p01_smoke_pipeline.sh
```

Result:

```text
ModelAuditTest: Ran 6 tests, OK
P01 dry-run generated a model audit report and continued because EXECUTE=0.
```

## Next Step

Run the P01 pipeline on the GPU host. It now uses `MODEL_PROFILE=p01` for the first download. After model download, the strict checkpoint audit must pass before P01 inference starts.
