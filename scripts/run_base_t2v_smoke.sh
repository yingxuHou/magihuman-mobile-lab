#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="${REPO_DIR:-${PROJECT_ROOT}/third_party/daVinci-MagiHuman}"
MODEL_ROOT="${MODEL_ROOT:-${PROJECT_ROOT}/models}"
RUN_DIR="${RUN_DIR:-${PROJECT_ROOT}/outputs/smoke-test}"
CONFIG_DIR="${CONFIG_DIR:-${PROJECT_ROOT}/run_configs}"

mkdir -p "${RUN_DIR}" "${CONFIG_DIR}" "${PROJECT_ROOT}/logs"

CONFIG_PATH="${CONFIG_DIR}/base_config.json"

python - "${REPO_DIR}/example/base/config.json" "${CONFIG_PATH}" "${MODEL_ROOT}" <<'PY'
import json
import pathlib
import sys

source = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])
model_root = pathlib.Path(sys.argv[3])

config = json.loads(source.read_text(encoding="utf-8"))
config["engine_config"]["load"] = str(model_root / "daVinci-MagiHuman" / "base")
config["evaluation_config"]["audio_model_path"] = str(model_root / "stable-audio-open-1.0")
config["evaluation_config"]["txt_model_path"] = str(model_root / "t5gemma-9b-9b-ul2")
config["evaluation_config"]["vae_model_path"] = str(model_root / "Wan2.2-TI2V-5B")
config["evaluation_config"]["student_config_path"] = str(
    model_root / "daVinci-MagiHuman" / "turbo_vae" / "TurboV3-Wan22-TinyShallow_7_7.json"
)
config["evaluation_config"]["student_ckpt_path"] = str(
    model_root / "daVinci-MagiHuman" / "turbo_vae" / "checkpoint-340000.ckpt"
)

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(config, indent=2), encoding="utf-8")
print(target)
PY

cd "${REPO_DIR}"

export MASTER_ADDR="${MASTER_ADDR:-localhost}"
export MASTER_PORT="${MASTER_PORT:-6013}"
export NNODES="${NNODES:-1}"
export NODE_RANK="${NODE_RANK:-0}"
export GPUS_PER_NODE="${GPUS_PER_NODE:-1}"
export WORLD_SIZE="$((GPUS_PER_NODE * NNODES))"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export NCCL_ALGO="${NCCL_ALGO:-^NVLS}"
export PYTHONPATH="${REPO_DIR}:${PYTHONPATH:-}"

DISTRIBUTED_ARGS="--nnodes=${NNODES} --node_rank=${NODE_RANK} --nproc_per_node=${GPUS_PER_NODE} --rdzv-backend=c10d --rdzv-endpoint=${MASTER_ADDR}:${MASTER_PORT}"
STAMP="$(date '+%Y%m%d_%H%M%S')"
LOG_PATH="${PROJECT_ROOT}/logs/base_t2v_${STAMP}.log"
SMI_LOG="${PROJECT_ROOT}/logs/base_t2v_${STAMP}_nvidia_smi.csv"
OUTPUT_PATH="${RUN_DIR}/base_t2v_${STAMP}"

nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu --format=csv -l 1 > "${SMI_LOG}" &
SMI_PID="$!"
trap 'kill "${SMI_PID}" >/dev/null 2>&1 || true' EXIT

if command -v /usr/bin/time >/dev/null 2>&1; then
  /usr/bin/time -v torchrun ${DISTRIBUTED_ARGS} inference/pipeline/entry.py \
    --config-load-path "${CONFIG_PATH}" \
    --prompt "$(<example/assets/prompt.txt)" \
    --seconds 4 \
    --br_width 448 \
    --br_height 256 \
    --output_path "${OUTPUT_PATH}" \
    2>&1 | tee "${LOG_PATH}"
else
  torchrun ${DISTRIBUTED_ARGS} inference/pipeline/entry.py \
    --config-load-path "${CONFIG_PATH}" \
    --prompt "$(<example/assets/prompt.txt)" \
    --seconds 4 \
    --br_width 448 \
    --br_height 256 \
    --output_path "${OUTPUT_PATH}" \
    2>&1 | tee "${LOG_PATH}"
fi

echo "output_path=${OUTPUT_PATH}"
echo "log_path=${LOG_PATH}"
echo "nvidia_smi_log=${SMI_LOG}"
