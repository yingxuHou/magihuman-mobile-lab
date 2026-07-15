# Stage 22: GPU Pipeline Hardening

Date: 2026-07-16

Status: complete for local tooling

## Goal

Reduce first-run failures on the Linux NVIDIA GPU host before spending time downloading hundreds of GiB of model weights or launching inference.

Stage 22 tightens the GPU path around three failure points:

- official source preparation
- Hugging Face gated-model authentication
- post-download model directory verification

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/gpu_preflight.py` | Adds Hugging Face auth checks, container `git` checks, and `--strict` failure mode |
| `tests/test_gpu_preflight.py` | Covers token detection and required-auth failures |
| `backend/gpu_bootstrap.py` | Passes `HF_TOKEN` and `HUGGINGFACE_HUB_TOKEN` into the generated Docker command |
| `scripts/gpu_reproduction_pipeline.sh` | Runs source preparation before preflight, checks auth before model download, and verifies model directories after download |
| `docs/stage-22-gpu-pipeline-hardening.md` | Records this stage |

## Updated GPU Host Flow

On the GPU host, set a Hugging Face token that has access to the gated external models:

```bash
export HF_TOKEN="<your_huggingface_token>"
```

Then run:

```bash
bash scripts/bootstrap_gpu_host.sh
bash outputs/run_magi_container.sh
```

Inside the container:

```bash
INSTALL_MAGICOMPILER=1 DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

The generated Docker command now passes through both supported token environment variables:

```bash
-e HF_TOKEN -e HUGGINGFACE_HUB_TOKEN
```

## Pipeline Order

The GPU pipeline now performs:

1. optional source preparation via `scripts/prepare_sources.sh`
2. preflight checks for GPU/container commands, source path, disk, and Hugging Face auth when downloads are requested
3. model downloads when `DOWNLOAD_MODELS=1`
4. post-download preflight requiring all expected model directories
5. experiment suite dry-run or execution
6. result summary, feasibility decision, and final report generation

## Current Limitation

This still does not produce runtime evidence on the current Windows workstation. It makes the remote GPU run less ambiguous by failing early if authentication, source checkout, model directories, or required runtime commands are missing.

## Validation

Commands:

```powershell
python -m unittest tests.test_gpu_preflight -v
PREPARE_SOURCES=0 MIN_DISK_GIB=0 bash scripts/gpu_reproduction_pipeline.sh
```

Result:

```text
GpuPreflightTest: Ran 7 tests, OK
Pipeline dry-run completed and reported not_ready for missing nvidia-smi/torchrun on this workstation.
```

## Next Step

Run the hardened pipeline on the Linux NVIDIA GPU host with `HF_TOKEN` set, then package and import the generated evidence.
