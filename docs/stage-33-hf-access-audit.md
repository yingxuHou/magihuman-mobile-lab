# Stage 33: Hugging Face Access Audit

Date: 2026-07-16

Status: local tooling complete; real GPU download still pending

## Goal

Before a GPU session spends time downloading 100+ GiB of checkpoints, verify that the configured Hugging Face token can access the exact model repositories and representative checkpoint files required by the selected run profile.

## What Changed

| File | Purpose |
| --- | --- |
| `backend/hf_access_audit.py` | Runs HEAD probes against required Hugging Face checkpoint files without downloading model weights |
| `scripts/run_p01_smoke_pipeline.sh` | Runs `profile=p01` access audit before `MODEL_PROFILE=p01` downloads |
| `scripts/gpu_reproduction_pipeline.sh` | Runs `profile=required_suite` access audit before required-suite downloads |
| `scripts/package_gpu_evidence.sh` | Includes `logs/*hf_access*.json` in the small GPU evidence package |
| `tests/test_hf_access_audit.py` | Covers token discovery, missing-token behavior, HTTP 403 handling, URL building, and Markdown output |

## Profiles

`p01` probes:

- `GAIR/daVinci-MagiHuman`: `base/model-00003-of-00007.safetensors`
- `GAIR/daVinci-MagiHuman`: `turbo_vae/checkpoint-340000.ckpt`
- `google/t5gemma-9b-9b-ul2`: `model-00007-of-00009.safetensors`
- `stabilityai/stable-audio-open-1.0`: `model.ckpt`
- `Wan-AI/Wan2.2-TI2V-5B`: `models_t5_umt5-xxl-enc-bf16.pth`

`required_suite` adds:

- `GAIR/daVinci-MagiHuman`: `540p_sr/model-00013-of-00013.safetensors`
- `GAIR/daVinci-MagiHuman`: `1080p_sr/model-00006-of-00013.safetensors`

`complete` also adds:

- `GAIR/daVinci-MagiHuman`: `distill/model-00012-of-00013.safetensors`

## GPU Host Usage

Run manually before downloads if debugging access:

```bash
export HF_TOKEN="<your_huggingface_token>"
python -m backend.hf_access_audit --profile p01 --format markdown
python -m backend.hf_access_audit --profile required_suite --format markdown
```

The P01 pipeline runs this automatically before checkpoint download:

```bash
INSTALL_MAGICOMPILER=1 DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/run_p01_smoke_pipeline.sh
```

The full pipeline runs the required-suite audit automatically:

```bash
INSTALL_MAGICOMPILER=1 DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

Set `HF_ACCESS_AUDIT=0` only for debugging network failures when access has already been verified another way.

## Report Outputs

P01 pipeline:

- `logs/p01_hf_access_<timestamp>.json`
- `outputs/reports/p01_hf_access_<timestamp>.md`

Full pipeline:

- `logs/hf_access_<timestamp>.json`
- `outputs/reports/hf_access_<timestamp>.md`

## Validation

Local validation does not call the network. It uses fake openers to test successful HEAD probes and HTTP failures.

```powershell
python -m unittest tests.test_hf_access_audit tests.test_pipeline_scripts tests.test_p01_smoke_pipeline -v
bash -n scripts/run_p01_smoke_pipeline.sh
bash -n scripts/gpu_reproduction_pipeline.sh
```

Results:

- Targeted Python tests: 11 passed.
- Bash syntax checks: passed.

## Current Limit

This stage verifies access tooling only. It does not prove checkpoint download completeness, GPU inference success, sample quality, mobile video compatibility, or cloud cost. Those remain pending until a Linux NVIDIA GPU host runs the P01 smoke pipeline and then the required full suite.
