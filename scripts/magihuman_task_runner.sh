#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="${REPO_DIR:-${PROJECT_ROOT}/third_party/daVinci-MagiHuman}"
MODEL_ROOT="${MODEL_ROOT:-${PROJECT_ROOT}/models}"
RUN_DIR="${RUN_DIR:-${PROJECT_ROOT}/outputs/worker-runs}"
CONFIG_DIR="${CONFIG_DIR:-${PROJECT_ROOT}/run_configs}"
LOG_DIR="${LOG_DIR:-${PROJECT_ROOT}/logs}"

TASK_ID="${MAGIHUMAN_TASK_ID:-manual}"
PROMPT_TEXT="${MAGIHUMAN_PROMPT:-}"
MODE="${MAGIHUMAN_MODE:-t2v}"
RESOLUTION="${MAGIHUMAN_RESOLUTION:-256p}"
DURATION_SECONDS="${MAGIHUMAN_DURATION_SECONDS:-5}"
SEED="${MAGIHUMAN_SEED:-42}"
RESULT_PATH="${MAGIHUMAN_RESULT_PATH:-}"
IMAGE_PATH="${MAGIHUMAN_IMAGE_PATH:-}"
AUDIO_PATH="${MAGIHUMAN_AUDIO_PATH:-}"
VARIANT="${MAGIHUMAN_MODEL_VARIANT:-base}"
CP_SIZE="${MAGIHUMAN_CP_SIZE:-1}"

if [ ! -d "${REPO_DIR}" ]; then
  echo "Missing REPO_DIR: ${REPO_DIR}" >&2
  exit 2
fi

if [ "${PROMPT_TEXT}" = "" ]; then
  PROMPT_TEXT="$(<"${REPO_DIR}/example/assets/prompt.txt")"
fi

if [ "${RESULT_PATH}" = "" ]; then
  echo "MAGIHUMAN_RESULT_PATH is required" >&2
  exit 2
fi

if [ "${MODE}" = "ti2v" ] && [ "${IMAGE_PATH}" = "" ]; then
  IMAGE_PATH="${REPO_DIR}/example/assets/image.png"
fi

mkdir -p "${RUN_DIR}" "${CONFIG_DIR}" "${LOG_DIR}" "$(dirname "${RESULT_PATH}")"

eval "$(
  python -m backend.magihuman_config \
    --repo-dir "${REPO_DIR}" \
    --model-root "${MODEL_ROOT}" \
    --config-dir "${CONFIG_DIR}" \
    --resolution "${RESOLUTION}" \
    --variant "${VARIANT}" \
    --cp-size "${CP_SIZE}" \
    --format shell
)"

cd "${REPO_DIR}"

export MASTER_ADDR="${MASTER_ADDR:-localhost}"
export MASTER_PORT="${MASTER_PORT:-${MAGIHUMAN_MASTER_PORT}}"
export NNODES="${NNODES:-1}"
export NODE_RANK="${NODE_RANK:-0}"
export GPUS_PER_NODE="${GPUS_PER_NODE:-1}"
export WORLD_SIZE="$((GPUS_PER_NODE * NNODES))"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export NCCL_ALGO="${NCCL_ALGO:-^NVLS}"
export PYTHONPATH="${REPO_DIR}:${PROJECT_ROOT}:${PYTHONPATH:-}"

if [ "${RESOLUTION}" = "1080p" ]; then
  export SR2_1080="${SR2_1080:-true}"
fi

if [ "${RESOLUTION}" != "256p" ]; then
  export CPU_OFFLOAD="${CPU_OFFLOAD:-true}"
fi

DISTRIBUTED_ARGS="--nnodes=${NNODES} --node_rank=${NODE_RANK} --nproc_per_node=${GPUS_PER_NODE} --rdzv-backend=c10d --rdzv-endpoint=${MASTER_ADDR}:${MASTER_PORT}"
STAMP="$(date '+%Y%m%d_%H%M%S')"
OUTPUT_PREFIX="${RUN_DIR}/${TASK_ID}_${RESOLUTION}_${MODE}_${STAMP}"
LOG_PATH="${LOG_DIR}/${TASK_ID}_${RESOLUTION}_${MODE}_${STAMP}.log"
SMI_LOG="${LOG_DIR}/${TASK_ID}_${RESOLUTION}_${MODE}_${STAMP}_nvidia_smi.csv"
METRICS_PATH="${LOG_DIR}/${TASK_ID}_${RESOLUTION}_${MODE}_${STAMP}_metrics.json"

SMI_PID=""
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu --format=csv -l 1 > "${SMI_LOG}" &
  SMI_PID="$!"
fi

cleanup() {
  if [ "${SMI_PID}" != "" ]; then
    kill "${SMI_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

ARGS=(
  torchrun
  ${DISTRIBUTED_ARGS}
  inference/pipeline/entry.py
  --config-load-path "${MAGIHUMAN_CONFIG_PATH}"
  --prompt "${PROMPT_TEXT}"
  --seed "${SEED}"
  --seconds "${DURATION_SECONDS}"
  --br_width "${MAGIHUMAN_BR_WIDTH}"
  --br_height "${MAGIHUMAN_BR_HEIGHT}"
  --output_path "${OUTPUT_PREFIX}"
)

if [ "${MAGIHUMAN_SR_WIDTH}" != "" ] && [ "${MAGIHUMAN_SR_HEIGHT}" != "" ]; then
  ARGS+=(--sr_width "${MAGIHUMAN_SR_WIDTH}" --sr_height "${MAGIHUMAN_SR_HEIGHT}")
fi

if [ "${MODE}" = "ti2v" ]; then
  ARGS+=(--image_path "${IMAGE_PATH}")
fi

if [ "${AUDIO_PATH}" != "" ]; then
  ARGS+=(--audio_path "${AUDIO_PATH}")
fi

if [ "${MAGI_COMPILER_OFFLOAD_ARGS:-}" != "" ]; then
  # shellcheck disable=SC2206
  OFFLOAD_ARGS=(${MAGI_COMPILER_OFFLOAD_ARGS})
  ARGS+=("${OFFLOAD_ARGS[@]}")
fi

if command -v /usr/bin/time >/dev/null 2>&1; then
  /usr/bin/time -v "${ARGS[@]}" 2>&1 | tee "${LOG_PATH}"
else
  "${ARGS[@]}" 2>&1 | tee "${LOG_PATH}"
fi

GENERATED_MP4="$(find "${RUN_DIR}" -maxdepth 1 -type f -name "$(basename "${OUTPUT_PREFIX}")*.mp4" -print | sort | tail -n 1)"
if [ "${GENERATED_MP4}" = "" ]; then
  echo "No generated mp4 found for prefix ${OUTPUT_PREFIX}" >&2
  exit 1
fi

cp "${GENERATED_MP4}" "${RESULT_PATH}"

METRICS_ARGS=(python -m backend.run_metrics --log "${LOG_PATH}" --video "${RESULT_PATH}" --output "${METRICS_PATH}")
if [ -f "${SMI_LOG}" ]; then
  METRICS_ARGS+=(--smi-csv "${SMI_LOG}")
fi

if command -v ffprobe >/dev/null 2>&1; then
  "${METRICS_ARGS[@]}" >/dev/null || true
fi

echo "generated_mp4=${GENERATED_MP4}"
echo "result_path=${RESULT_PATH}"
echo "log_path=${LOG_PATH}"
echo "nvidia_smi_log=${SMI_LOG}"
echo "metrics_path=${METRICS_PATH}"
echo "metrics_command=python -m backend.run_metrics --log ${LOG_PATH} --smi-csv ${SMI_LOG} --video ${RESULT_PATH} --output ${METRICS_PATH}"
