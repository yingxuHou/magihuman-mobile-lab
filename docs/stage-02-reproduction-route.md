# Stage 02: Reproduction Route Decision

Date: 2026-07-15

Status: complete

## Goal

Choose the practical reproduction route after official verification and local environment inspection.

## Inputs

Stage 00 established:

- Official model stack is about 201.27 GiB before external models.
- Official README recommends Docker image `sandai/magi-human:latest`.
- Official speed numbers are reported on a single H100 GPU.
- Official examples run through `torchrun` and `inference/pipeline/entry.py`.

Stage 01 established:

- Current workstation has Intel Iris Xe Graphics only.
- `nvidia-smi`, `nvcc`, Docker, Conda, and torch are unavailable.
- Python is 3.8.6, while the official README requires Python 3.12+.
- D drive free space is about 169.36 GiB, smaller than the official model stack before external models.

## Decision

Use this local repository for orchestration, documentation, source inspection, runbook creation, and GitHub synchronization.

Use a separate Linux NVIDIA GPU machine for actual inference reproduction.

Priority order:

1. H100 GPU machine with Docker and NVIDIA Container Toolkit.
2. Other high-VRAM NVIDIA GPU machine using Docker.
3. Conda setup only if Docker is unavailable or source-level debugging is required.

## Why Local Full Reproduction Is Not Attempted

Local full inference is not a productive route because:

- No NVIDIA GPU is available.
- CUDA tooling is absent.
- Docker is absent.
- Conda is absent.
- Python version does not match official requirements.
- Disk space is smaller than the official full model stack.

Trying to force local execution would not generate meaningful inference data for mobile feasibility.

## Target Cloud GPU Baseline

Recommended target:

- Linux host.
- NVIDIA H100 if the goal is to compare against official speed numbers.
- At least 500 GiB disk for checkpoints, external models, cache, logs, and generated videos.
- Docker installed.
- NVIDIA Container Toolkit installed.
- Working `nvidia-smi` inside and outside Docker.

Acceptable exploratory target:

- A100, RTX 4090, RTX 5090, or multi-GPU NVIDIA server.
- Must expect slower runtime or memory offload.
- Must record exact GPU, VRAM, CPU offload settings, and `engine_config.cp_size`.

## Reproduction Path

On the GPU machine:

1. Clone this repo.
2. Run `scripts/check_env.ps1` on Windows or equivalent Linux checks.
3. Pull `sandai/magi-human:latest`.
4. Clone official source into `third_party/`.
5. Download the model stack and external models.
6. Update `example/*/config.json` checkpoint paths.
7. Run `example/base/run_T2V.sh` first.
8. Record latency, peak VRAM, command, logs, and output path.
9. Only after 256p succeeds, test distill, 540p SR, and 1080p SR.

## Current Mobile Feasibility Impact

This route decision strengthens the likely cloud-backend direction but still does not complete the final conclusion.

Current evidence against direct mobile packaging:

- Full model stack is about 201.27 GiB.
- Base checkpoint group is about 28.54 GiB.
- Official stack assumes CUDA/PyTorch/MagiCompiler/Flash Attention.
- Official benchmark uses H100.

Still missing:

- Actual 256p latency and peak VRAM.
- Actual 1080p latency and peak VRAM.
- Whether any export path exists for ONNX/Core ML/NCNN/MNN.
- Output quality from reproduced samples.

## Next Step

Prepare source-code inspection and scripts:

- Clone official repositories into ignored `third_party/`.
- Record upstream commits.
- Add Linux cloud setup scripts.
- Add model download scripts.
- Add smoke-test command wrappers.
