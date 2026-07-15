#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

PYTHON_BIN="${PYTHON:-python}"
LOG_DIR="${LOG_DIR:-logs}"
RESULT_DIR="${RESULT_DIR:-outputs/experiment-results}"
MODEL_ROOT="${MODEL_ROOT:-models}"
REPO_DIR="${REPO_DIR:-third_party/daVinci-MagiHuman}"
MODE="${MODE:-container}"
MIN_DISK_GIB="${MIN_DISK_GIB:-500}"
EXECUTE="${EXECUTE:-0}"
DOWNLOAD_MODELS="${DOWNLOAD_MODELS:-0}"
INCLUDE_OPTIONAL="${INCLUDE_OPTIONAL:-0}"
STAMP="$(date '+%Y%m%d_%H%M%S')"

mkdir -p "${LOG_DIR}" "${RESULT_DIR}" outputs/reports

PREFLIGHT_ARGS=(
  -m backend.gpu_preflight
  --mode "${MODE}"
  --project-root "${PROJECT_ROOT}"
  --repo-dir "${REPO_DIR}"
  --model-root "${MODEL_ROOT}"
  --min-disk-gib "${MIN_DISK_GIB}"
)

if [ "${EXECUTE}" = "1" ]; then
  PREFLIGHT_ARGS+=(--require-models)
fi

"${PYTHON_BIN}" "${PREFLIGHT_ARGS[@]}" --format json --output "${LOG_DIR}/gpu_preflight_${STAMP}.json"
"${PYTHON_BIN}" "${PREFLIGHT_ARGS[@]}" --format markdown --output "outputs/reports/gpu_preflight_${STAMP}.md"

if [ "${DOWNLOAD_MODELS}" = "1" ]; then
  MODEL_ROOT="${MODEL_ROOT}" bash scripts/download_models.sh 2>&1 | tee "${LOG_DIR}/download_models_${STAMP}.log"
fi

SUITE_ARGS=(--log-dir "${LOG_DIR}" --result-dir "${RESULT_DIR}")
if [ "${INCLUDE_OPTIONAL}" = "1" ]; then
  SUITE_ARGS+=(--include-optional)
fi

if [ "${EXECUTE}" = "1" ]; then
  bash scripts/run_experiment_suite.sh --execute "${SUITE_ARGS[@]}" 2>&1 | tee "${LOG_DIR}/experiment_suite_${STAMP}.log"
else
  FORMAT=shell bash scripts/run_experiment_suite.sh "${SUITE_ARGS[@]}" 2>&1 | tee "${LOG_DIR}/experiment_suite_dryrun_${STAMP}.sh"
fi

"${PYTHON_BIN}" -m backend.experiment_results --log-dir "${LOG_DIR}" --format markdown \
  --output "outputs/reports/experiment_results_${STAMP}.md"
"${PYTHON_BIN}" -m backend.feasibility_decision --log-dir "${LOG_DIR}" --format markdown \
  | tee "outputs/reports/feasibility_decision_${STAMP}.md"

echo "preflight_json=${LOG_DIR}/gpu_preflight_${STAMP}.json"
echo "preflight_report=outputs/reports/gpu_preflight_${STAMP}.md"
echo "experiment_report=outputs/reports/experiment_results_${STAMP}.md"
echo "feasibility_report=outputs/reports/feasibility_decision_${STAMP}.md"
