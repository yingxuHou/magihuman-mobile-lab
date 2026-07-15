# Stage 01: Local Environment Check

Date: 2026-07-15

Status: complete

## Goal

Check whether the current workstation can run the official daVinci-MagiHuman reproduction locally.

## Command Results

| Check | Command | Result |
| --- | --- | --- |
| NVIDIA GPU tool | `nvidia-smi` | Not found |
| CUDA compiler | `nvcc --version` | Not found |
| Git | `git --version` | `git version 2.50.1.windows.1` |
| Git LFS | `git lfs version` | `git-lfs/3.7.0` |
| Conda | `conda --version` | Not found |
| Docker | `docker --version` | Not found |
| ffmpeg | `ffmpeg -version` | `ffmpeg version 8.0.1-full_build-www.gyan.dev` |
| Python | `python --version` | `Python 3.8.6` |
| PyTorch | `python -c "import torch"` | Not installed |

## Hardware Snapshot

| Item | Value |
| --- | --- |
| OS | Microsoft Windows 11 Home China 10.0.26200, 64-bit |
| Display GPU | Intel(R) Iris(R) Xe Graphics |
| GPU memory reported by Windows | 2,147,479,552 bytes |
| NVIDIA GPU | Not detected |
| D drive free space | 181,887,066,112 bytes, about 169.36 GiB |

## Decision

This machine is not suitable for local full inference reproduction.

Reasons:

- No NVIDIA GPU was detected.
- `nvidia-smi` and `nvcc` are unavailable.
- Docker is not installed or not on PATH.
- Conda is not installed or not on PATH.
- Current Python is 3.8.6, while the official README requires Python 3.12+.
- PyTorch is not installed.
- D drive free space is about 169.36 GiB, which is smaller than the 201.27 GiB official model stack before external models.

## What Can Still Be Done Locally

- Inspect official source code.
- Prepare scripts and runbooks.
- Clone upstream repositories into ignored `third_party/`.
- Download a subset of small metadata files if needed.
- Maintain reports and GitHub sync.
- Design backend and mobile integration architecture.

## What Requires Another Environment

- Full model checkpoint download.
- CUDA runtime validation.
- MagiCompiler/Flash Attention validation.
- 256p smoke-test inference.
- 540p/1080p super-resolution inference.
- Peak VRAM and latency measurements.

## Next Step

Prepare source-code inspection and a cloud GPU runbook. The likely reproduction target should be a Linux GPU environment with:

- NVIDIA GPU and working `nvidia-smi`.
- Docker with NVIDIA Container Toolkit, or Conda with Python 3.12.
- Enough disk for at least the base checkpoint plus external models.
- Preferably H100 if we want to compare against official speed metrics.
