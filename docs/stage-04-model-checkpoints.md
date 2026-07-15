# Stage 04: Model Checkpoint Plan

Date: 2026-07-15

Status: complete for metadata and download strategy

## Goal

Identify all required model files, estimate storage requirements, and decide where checkpoint download should happen.

## Main Model Stack

Source: `GAIR/daVinci-MagiHuman`

| Item | Value |
| --- | --- |
| HF sha | `7fe95e50c11bd92bdadf94cd51dbec18427f8e0c` |
| Last modified | 2026-03-25 14:00:27 UTC |
| Gated | No |
| License tag | Apache 2.0 |
| File count | 56 |
| Total size | 201.27 GiB |
| Largest file | `base/model-00003-of-00007.safetensors` |
| Largest file size | 4.66 GiB |

Main model groups:

| Group | Files | Size | Largest file |
| --- | ---: | ---: | --- |
| `base` | 8 | 28.54 GiB | `base/model-00003-of-00007.safetensors` |
| `distill` | 14 | 56.99 GiB | `distill/model-00012-of-00013.safetensors` |
| `540p_sr` | 14 | 56.99 GiB | `540p_sr/model-00013-of-00013.safetensors` |
| `1080p_sr` | 14 | 56.99 GiB | `1080p_sr/model-00006-of-00013.safetensors` |
| `turbo_vae` | 2 | 1.74 GiB | `turbo_vae/checkpoint-340000.ckpt` |

## External Models

Required by official example configs:

| Model | Gate | Files | Size | Largest file |
| --- | --- | ---: | ---: | --- |
| `google/t5gemma-9b-9b-ul2` | manual gated | 18 | 37.91 GiB | `model-00007-of-00009.safetensors` |
| `stabilityai/stable-audio-open-1.0` | auto gated | 25 | 14.60 GiB | `model.ckpt` |
| `Wan-AI/Wan2.2-TI2V-5B` | no gate | 23 | 31.85 GiB | `models_t5_umt5-xxl-enc-bf16.pth` |

Total external dependency size: about 84.36 GiB.

Total estimated checkpoint size for the complete stack: about 285.63 GiB before cache, logs, and outputs.

## Minimum Smoke-Test Storage

Base 256p T2V still requires:

- `daVinci-MagiHuman/base`: 28.54 GiB.
- `daVinci-MagiHuman/turbo_vae`: 1.74 GiB.
- `google/t5gemma-9b-9b-ul2`: 37.91 GiB.
- `stabilityai/stable-audio-open-1.0`: 14.60 GiB.
- `Wan-AI/Wan2.2-TI2V-5B`: 31.85 GiB.

Estimated base smoke-test checkpoint footprint: about 114.64 GiB before cache and outputs.

## Local Download Decision

Do not download checkpoints on the current workstation.

Reasons:

- No NVIDIA GPU or CUDA runtime is available locally.
- Docker and Conda are not available locally.
- The full stack is larger than current D drive free space.
- Two external model repositories are gated and require Hugging Face authentication or terms acceptance.

## Cloud Download Strategy

Run downloads on the GPU machine:

```bash
MODEL_ROOT=models bash scripts/download_models.sh
```

Before running:

- Confirm Hugging Face login with `huggingface-cli whoami`.
- Confirm access to `google/t5gemma-9b-9b-ul2`.
- Confirm access to `stabilityai/stable-audio-open-1.0`.
- Confirm at least 500 GiB free disk.

## Mobile Feasibility Impact

Checkpoint size alone rules out bundling the full model stack in a normal mobile app package.

This does not yet prove whether a smaller derivative or separate mobile-specific model could exist. It does strongly support the architecture direction where the phone is a client and inference runs on a server.

## Next Step

On a GPU machine, run:

1. `scripts/cloud_env_check.sh`
2. `scripts/download_models.sh`
3. `scripts/run_base_t2v_smoke.sh`
