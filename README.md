# MagiHuman Mobile Lab

`magihuman-mobile-lab`

MagiHuman Mobile Lab is an experimental reproduction and feasibility project for daVinci-MagiHuman. The goal is to run the official model, collect measurable inference data, and decide whether it can be integrated into a mobile app.

This repository tracks:

- official source and model verification
- environment setup notes
- GPU memory, latency, model size, and output quality measurements
- 256p and 1080p reproduction experiments
- mobile app feasibility analysis
- a possible cloud GPU backend architecture for mobile clients

The working assumption is that the full daVinci-MagiHuman model is unlikely to run directly on phones because it is a large GPU-oriented generative video model. That is not treated as the final conclusion. The final decision must be backed by reproduction data, including model size, peak VRAM, inference latency, dependency requirements, and available mobile export paths.

Official references:

- Paper: https://arxiv.org/abs/2603.21986
- Code: https://github.com/GAIR-NLP/daVinci-MagiHuman
- Model: https://huggingface.co/GAIR/daVinci-MagiHuman
- Demo: https://huggingface.co/spaces/SII-GAIR/daVinci-MagiHuman

## Current Plan

1. Verify the official paper, code, model files, license, and inference commands.
2. Check the local machine GPU, CUDA, Docker, Conda, ffmpeg, and disk space.
3. Prefer Docker reproduction first, then fall back to Conda if needed.
4. Run the smallest 5-second 256p smoke test.
5. Record command lines, output paths, peak VRAM, latency, and failure modes.
6. Test higher resolutions and super-resolution only after the 256p path works.
7. Use the measured data to decide between on-device inference, cloud GPU inference, or stopping the app integration attempt.

Large files such as model weights, generated videos, and cloned third-party repositories should not be committed directly.

## Current Status

- Stage 00 official verification is complete.
- Stage 01 local environment check is complete.
- Stage 02 route decision is complete.
- Local full inference is not viable on the current workstation because no NVIDIA GPU/CUDA/Docker/Conda environment is available.
- Actual inference reproduction should run on a Linux NVIDIA GPU machine, preferably H100, using the official Docker image `sandai/magi-human:latest`.
- Stage 06 added a local API prototype for the mobile-client/cloud-GPU architecture.
- Stage 07 added a worker prototype for queued task execution.
- Stage 08 added a worker-compatible MagiHuman task runner and config generator.
- Stage 09 added run-metrics parsing for `nvidia-smi`, `/usr/bin/time -v`, and `ffprobe`. The backend prototype now passes 18 local tests using Python standard library only.
- Stage 10 added an experiment matrix for performance and multilingual runs. The backend prototype now passes 23 local tests using Python standard library only.
- Stage 11 added experiment result aggregation for metrics JSON files. The backend prototype now passes 27 local tests using Python standard library only.
- Stage 12 added a case-level experiment runner with dependency checks. The backend prototype now passes 32 local tests using Python standard library only.
- Stage 13 added retry and result-retention cleanup policies. The backend prototype now passes 35 local tests using Python standard library only.
- Stage 14 added a repeatable feasibility decision generator. The backend prototype now passes 38 local tests using Python standard library only.
- Stage 15 added a required GPU experiment suite runner for P01/P03/P04/T01/T02. The backend prototype now passes 43 local tests using Python standard library only.
- Stage 16 added GPU preflight checks and a pipeline script for cloud reproduction. The backend prototype now passes 48 local tests using Python standard library only.
- Stage 17 added a structured generated-sample quality review gate. The backend prototype now passes 55 local tests using Python standard library only.
- Stage 18 added a cost and wait-time review gate. The backend prototype now passes 64 local tests using Python standard library only.
- Stage 19 added a combined final feasibility report generator. The backend prototype now passes 69 local tests using Python standard library only.
- Stage 20 added GPU evidence packaging and import-audit tooling. The backend prototype now passes 74 local tests using Python standard library only.

## Current Mobile Feasibility Decision

Run:

```powershell
python -m backend.feasibility_decision --log-dir logs --format markdown
```

Current output is `B_pending_runtime`:

- A. Official on-device inference is `not_viable` based on model size, CUDA/server-GPU dependencies, and no visible official mobile export route.
- B. Mobile app plus cloud GPU backend is `pending_runtime_evidence` until P01/P03/P04/T01/T02 metrics, sample quality review, and cost review exist.
- C. Stopping productization is `not_decided` because the cloud GPU path has not been measured yet.

Plan the required GPU suite:

```powershell
python -m backend.experiment_suite --log-dir logs --format markdown
```

Execute it on a prepared Linux NVIDIA GPU host:

```bash
bash scripts/run_experiment_suite.sh --execute
```

Or run the full GPU-host pipeline:

```bash
DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

Create a quality review template after samples exist:

```powershell
python -m backend.quality_review --create-template --output docs/quality-review.json
```

Create a cost review template after runtime metrics exist:

```powershell
python -m backend.cost_review --create-template --output docs/cost-review.json
```

Generate the combined report:

```powershell
python -m backend.final_report --log-dir logs --format markdown --output docs/mobile-feasibility-report.md
```

Audit imported GPU evidence:

```powershell
python -m backend.evidence_import --log-dir logs --final-report-output docs/mobile-feasibility-report.md --format markdown --output docs/gpu-evidence-import-audit.md
```
