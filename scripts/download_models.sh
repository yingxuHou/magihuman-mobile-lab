#!/usr/bin/env bash
set -euo pipefail

MODEL_ROOT="${MODEL_ROOT:-models}"
MODEL_PROFILE="${MODEL_PROFILE:-complete}"
DRY_RUN="${DRY_RUN:-0}"

mkdir -p "${MODEL_ROOT}"

if ! command -v huggingface-cli >/dev/null 2>&1; then
  if [ "${DRY_RUN}" = "1" ]; then
    echo "python -m pip install -U huggingface_hub"
  else
    python -m pip install -U huggingface_hub
  fi
fi

download() {
  if [ "${DRY_RUN}" = "1" ]; then
    printf '%q ' "$@"
    printf '\n'
  else
    "$@"
  fi
}

download_magihuman() {
  case "${MODEL_PROFILE}" in
    p01)
      echo "Downloading daVinci-MagiHuman P01 groups to ${MODEL_ROOT}/daVinci-MagiHuman"
      download huggingface-cli download GAIR/daVinci-MagiHuman \
        --include "base/*" \
        --include "turbo_vae/*" \
        --local-dir "${MODEL_ROOT}/daVinci-MagiHuman"
      ;;
    required_suite)
      echo "Downloading daVinci-MagiHuman required-suite groups to ${MODEL_ROOT}/daVinci-MagiHuman"
      download huggingface-cli download GAIR/daVinci-MagiHuman \
        --include "base/*" \
        --include "turbo_vae/*" \
        --include "540p_sr/*" \
        --include "1080p_sr/*" \
        --local-dir "${MODEL_ROOT}/daVinci-MagiHuman"
      ;;
    complete)
      echo "Downloading complete daVinci-MagiHuman model stack to ${MODEL_ROOT}/daVinci-MagiHuman"
      download huggingface-cli download GAIR/daVinci-MagiHuman \
        --local-dir "${MODEL_ROOT}/daVinci-MagiHuman"
      ;;
    *)
      echo "Unknown MODEL_PROFILE: ${MODEL_PROFILE}. Use p01, required_suite, or complete." >&2
      exit 2
      ;;
  esac
}

download_magihuman

echo "Downloading text encoder to ${MODEL_ROOT}/t5gemma-9b-9b-ul2"
download huggingface-cli download google/t5gemma-9b-9b-ul2 \
  --local-dir "${MODEL_ROOT}/t5gemma-9b-9b-ul2"

echo "Downloading audio model to ${MODEL_ROOT}/stable-audio-open-1.0"
download huggingface-cli download stabilityai/stable-audio-open-1.0 \
  --local-dir "${MODEL_ROOT}/stable-audio-open-1.0"

echo "Downloading VAE to ${MODEL_ROOT}/Wan2.2-TI2V-5B"
download huggingface-cli download Wan-AI/Wan2.2-TI2V-5B \
  --local-dir "${MODEL_ROOT}/Wan2.2-TI2V-5B"

if [ "${DRY_RUN}" = "1" ]; then
  echo "du -sh ${MODEL_ROOT}/*"
else
  du -sh "${MODEL_ROOT}"/*
fi
