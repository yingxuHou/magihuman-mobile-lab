# Mobile Feasibility

This document will hold the final mobile app integration conclusion after reproduction data is collected.

## Current Status

The current statement is a hypothesis, not a final conclusion:

- Full on-device inference is unlikely because daVinci-MagiHuman is described as a 15B-parameter GPU-oriented video generation model.
- The likely product architecture is a mobile client connected to a GPU backend.
- Stage 00 added package-size evidence: the official model stack listed on Hugging Face is about 201.27 GiB before external models, and the base checkpoint group alone is about 28.54 GiB.

## Required Evidence

- Model weight size
- Peak VRAM
- 256p inference latency
- 1080p inference latency
- CUDA and NVIDIA GPU dependency
- Availability of ONNX, Core ML, NCNN, MNN, or other mobile export paths
- Output quality from reproduced samples

## Evidence Collected

| Date | Evidence | Impact |
| --- | --- | --- |
| 2026-07-15 | HF model stack is about 201.27 GiB across 56 files | Strong evidence against bundling the full model in a normal mobile app package |
| 2026-07-15 | Official README uses CUDA/PyTorch/MagiCompiler/Flash Attention and reports H100 performance | Strong evidence that normal mobile CPUs/NPUs are not the target runtime |
