# Stage 37: Checkpoint Download Log Audit

Date: 2026-07-16

Status: complete for local tooling; real GPU download audit still pending

## Goal

The first P01 GPU run should not download the full checkpoint stack. It should download only the P01-required main groups, plus the external text/audio/VAE models. Stage 37 makes the download command auditable and blocks the pipeline if the logged commands do not match the selected download profile.

## What Changed

| File | Purpose |
| --- | --- |
| `scripts/download_models.sh` | Prints every download command as `download_command=...` before executing it |
| `backend/download_log_audit.py` | Audits logged Hugging Face download commands for `p01`, `required_suite`, or `complete` profiles |
| `scripts/run_p01_smoke_pipeline.sh` | Audits `logs/p01_download_models_<timestamp>.log` after checkpoint download |
| `scripts/gpu_reproduction_pipeline.sh` | Audits `logs/download_models_<timestamp>.log` after required-suite download |
| `backend/pipeline_artifact_audit.py` | Requires download log audit files when `DOWNLOAD_MODELS=1` |
| `scripts/package_gpu_evidence.sh` | Includes `logs/*download_log_audit*.json` in the GPU evidence package |
| `tests/test_download_log_audit.py` | Covers P01, required-suite, forbidden SR/distill, missing external repos, and Markdown output |

## P01 Rules

`profile=p01` requires:

- `GAIR/daVinci-MagiHuman --include base/*`
- `GAIR/daVinci-MagiHuman --include turbo_vae/*`
- `google/t5gemma-9b-9b-ul2`
- `stabilityai/stable-audio-open-1.0`
- `Wan-AI/Wan2.2-TI2V-5B`

It forbids:

- `540p_sr/*`
- `1080p_sr/*`
- `distill/*`

## Required-Suite Rules

`profile=required_suite` requires:

- `base/*`
- `turbo_vae/*`
- `540p_sr/*`
- `1080p_sr/*`
- the three external repositories

It forbids:

- `distill/*`

## Pipeline Outputs

P01 pipeline:

- `logs/p01_download_log_audit_<timestamp>.json`
- `outputs/reports/p01_download_log_audit_<timestamp>.md`

Full pipeline:

- `logs/download_log_audit_<timestamp>.json`
- `outputs/reports/download_log_audit_<timestamp>.md`

## Validation

```powershell
python -m unittest tests.test_download_log_audit tests.test_download_models_script tests.test_pipeline_scripts tests.test_pipeline_artifact_audit tests.test_evidence_package -v
bash -n scripts/download_models.sh
bash -n scripts/run_p01_smoke_pipeline.sh
bash -n scripts/gpu_reproduction_pipeline.sh
bash -n scripts/package_gpu_evidence.sh
```

Result:

- Targeted tests: 21 passed.
- Bash syntax checks: passed.

## Current Limit

The audit validates logged download commands. It does not prove the files downloaded completely; that remains the job of `backend.model_audit.py` after download.
