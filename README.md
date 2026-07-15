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
- Stage 06 added a local API prototype for the mobile-client/cloud-GPU architecture. It passed 6 local tests using Python standard library only.
