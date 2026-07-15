# Stage 05: 256p Smoke-Test Readiness

Date: 2026-07-15

Status: prepared, not executed

## Goal

Run the smallest official 256p generation path and collect the first real inference measurements.

This stage cannot be marked as reproduced until a GPU machine generates an output video.

## Selected First Test

Use official base T2V path:

```bash
example/base/run_T2V.sh
```

Equivalent project wrapper:

```bash
MODEL_ROOT=models bash scripts/magihuman_task_runner.sh
```

Preferred current smoke pipeline:

```bash
INSTALL_MAGICOMPILER=1 DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/run_p01_smoke_pipeline.sh
```

This preferred path prepares sources, checks Hugging Face access when downloading models, verifies model directories after download, runs only P01, and writes the same summary/decision reports used by later stages.

## Why Base T2V First

- It avoids reference image complexity.
- It avoids super-resolution first.
- It is the closest minimal path to the official 256p benchmark.
- It establishes that the main model, text encoder, audio model, VAE, and Turbo VAE paths are all valid.

## Required Inputs

| Input | Source |
| --- | --- |
| Prompt | `third_party/daVinci-MagiHuman/example/assets/prompt.txt` |
| Config template | `third_party/daVinci-MagiHuman/example/base/config.json` |
| Base checkpoint | `models/daVinci-MagiHuman/base` |
| Turbo VAE | `models/daVinci-MagiHuman/turbo_vae` |
| Text encoder | `models/t5gemma-9b-9b-ul2` |
| Audio model | `models/stable-audio-open-1.0` |
| VAE | `models/Wan2.2-TI2V-5B` |

## Measurements To Capture

| Metric | Method |
| --- | --- |
| GPU model | `nvidia-smi` |
| Peak VRAM | `nvidia-smi --query-gpu=... -l 1` captured by script |
| Wall time | `/usr/bin/time -v` when available |
| CPU memory | `/usr/bin/time -v` maximum resident set size |
| Output path | Printed by `scripts/magihuman_task_runner.sh` |
| Log path | Printed by `scripts/magihuman_task_runner.sh` |
| Video validity | open/play mp4; later verify with `ffprobe` |

## Current Blocker

The current workstation cannot run this stage:

- No NVIDIA GPU.
- No CUDA.
- No Docker.
- No Conda.
- No PyTorch.

This is an environment limitation, not a model reproduction result.

## Pass Criteria

The smoke test passes only when:

- A video file is generated.
- The file is playable.
- The output duration is close to the requested duration.
- Audio exists.
- The log contains no fatal runtime error.
- GPU memory and wall time are recorded.

## Failure Criteria

Record failure if:

- Model download is incomplete.
- Any external gated model cannot be accessed.
- CUDA/Flash Attention/MagiCompiler fails to load.
- The job OOMs.
- The output is corrupt, black, silent, or missing.

## Next Execution Environment

Run this stage on a Linux NVIDIA GPU machine, preferably H100 if the goal is to compare with official timing.

Minimum first commands:

```bash
git clone https://github.com/yingxuHou/magihuman-mobile-lab.git
cd magihuman-mobile-lab
export HF_TOKEN="<your_huggingface_token>"
bash scripts/bootstrap_gpu_host.sh
bash outputs/run_magi_container.sh
INSTALL_MAGICOMPILER=1 DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/run_p01_smoke_pipeline.sh
```

After execution, update:

- `docs/reproduction-log.md`
- `docs/mobile-feasibility.md`
- this report with actual metrics
- `7.15-todolist.md`
