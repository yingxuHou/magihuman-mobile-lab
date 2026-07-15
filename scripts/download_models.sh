#!/usr/bin/env bash
set -euo pipefail

MODEL_ROOT="${MODEL_ROOT:-models}"

mkdir -p "${MODEL_ROOT}"

if ! command -v huggingface-cli >/dev/null 2>&1; then
  python -m pip install -U huggingface_hub
fi

echo "Downloading daVinci-MagiHuman model stack to ${MODEL_ROOT}/daVinci-MagiHuman"
huggingface-cli download GAIR/daVinci-MagiHuman \
  --local-dir "${MODEL_ROOT}/daVinci-MagiHuman"

echo "Downloading text encoder to ${MODEL_ROOT}/t5gemma-9b-9b-ul2"
huggingface-cli download google/t5gemma-9b-9b-ul2 \
  --local-dir "${MODEL_ROOT}/t5gemma-9b-9b-ul2"

echo "Downloading audio model to ${MODEL_ROOT}/stable-audio-open-1.0"
huggingface-cli download stabilityai/stable-audio-open-1.0 \
  --local-dir "${MODEL_ROOT}/stable-audio-open-1.0"

echo "Downloading VAE to ${MODEL_ROOT}/Wan2.2-TI2V-5B"
huggingface-cli download Wan-AI/Wan2.2-TI2V-5B \
  --local-dir "${MODEL_ROOT}/Wan2.2-TI2V-5B"

du -sh "${MODEL_ROOT}"/*
