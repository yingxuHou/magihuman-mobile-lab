# Mobile Feasibility

This document will hold the final mobile app integration conclusion after reproduction data is collected.

## Current Status

The current statement is a hypothesis, not a final conclusion:

- Full on-device inference is unlikely because daVinci-MagiHuman is described as a 15B-parameter GPU-oriented video generation model.
- The likely product architecture is a mobile client connected to a GPU backend.

## Required Evidence

- Model weight size
- Peak VRAM
- 256p inference latency
- 1080p inference latency
- CUDA and NVIDIA GPU dependency
- Availability of ONNX, Core ML, NCNN, MNN, or other mobile export paths
- Output quality from reproduced samples

