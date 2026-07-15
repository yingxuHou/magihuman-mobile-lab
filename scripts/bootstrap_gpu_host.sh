#!/usr/bin/env bash
set -euo pipefail

DOCKER_IMAGE="${DOCKER_IMAGE:-sandai/magi-human:latest}"
CONTAINER_NAME="${CONTAINER_NAME:-magihuman-lab}"
PULL_DOCKER="${PULL_DOCKER:-1}"
RUN_CONTAINER="${RUN_CONTAINER:-0}"

mkdir -p third_party models outputs logs outputs/reports

python -m backend.gpu_preflight --mode host --format markdown --output outputs/reports/gpu_host_preflight.md
python -m backend.gpu_bootstrap \
  --image "${DOCKER_IMAGE}" \
  --container-name "${CONTAINER_NAME}" \
  --format markdown \
  --output outputs/reports/gpu_bootstrap_plan.md
python -m backend.gpu_bootstrap \
  --image "${DOCKER_IMAGE}" \
  --container-name "${CONTAINER_NAME}" \
  --format shell \
  --output outputs/run_magi_container.sh
chmod +x outputs/run_magi_container.sh

if [ "${PULL_DOCKER}" = "1" ]; then
  docker pull "${DOCKER_IMAGE}"
fi

echo "preflight_report=outputs/reports/gpu_host_preflight.md"
echo "bootstrap_plan=outputs/reports/gpu_bootstrap_plan.md"
echo "container_launcher=outputs/run_magi_container.sh"

if [ "${RUN_CONTAINER}" = "1" ]; then
  bash outputs/run_magi_container.sh
fi
