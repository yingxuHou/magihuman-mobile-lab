#!/usr/bin/env bash
set -u

run_check() {
  local name="$1"
  shift
  echo "## ${name}"
  "$@" || echo "FAILED: ${name}"
  echo
}

run_check "nvidia-smi" nvidia-smi
run_check "docker" docker --version
run_check "docker-gpu" docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
run_check "git" git --version
run_check "git-lfs" git lfs version
run_check "python3" python3 --version
run_check "disk" df -h
