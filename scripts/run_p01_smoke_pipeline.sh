#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

PYTHON_BIN="${PYTHON:-python}"
LOG_DIR="${LOG_DIR:-logs}"
RESULT_DIR="${RESULT_DIR:-outputs/smoke-test}"
MODEL_ROOT="${MODEL_ROOT:-models}"
REPO_DIR="${REPO_DIR:-third_party/daVinci-MagiHuman}"
MODE="${MODE:-container}"
MIN_DISK_GIB="${MIN_DISK_GIB:-500}"
EXECUTE="${EXECUTE:-0}"
DOWNLOAD_MODELS="${DOWNLOAD_MODELS:-0}"
PREPARE_SOURCES="${PREPARE_SOURCES:-1}"
RERUN="${RERUN:-0}"
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

run_preflight() {
  local suffix="$1"
  local require_models="$2"
  local strict="$3"
  local args=("${PREFLIGHT_ARGS[@]}")

  if [ "${require_models}" = "1" ]; then
    args+=(--require-models)
  fi
  if [ "${DOWNLOAD_MODELS}" = "1" ]; then
    args+=(--require-hf-auth)
  fi
  if [ "${strict}" = "1" ]; then
    args+=(--strict)
  fi

  "${PYTHON_BIN}" "${args[@]}" --format json --output "${LOG_DIR}/p01_preflight_${suffix}.json"
  "${PYTHON_BIN}" "${args[@]}" --format markdown --output "outputs/reports/p01_preflight_${suffix}.md"
}

if [ "${PREPARE_SOURCES}" = "1" ]; then
  bash scripts/prepare_sources.sh 2>&1 | tee "${LOG_DIR}/p01_prepare_sources_${STAMP}.log"
fi

INITIAL_REQUIRE_MODELS=0
if [ "${EXECUTE}" = "1" ] && [ "${DOWNLOAD_MODELS}" != "1" ]; then
  INITIAL_REQUIRE_MODELS=1
fi

INITIAL_STRICT=0
if [ "${EXECUTE}" = "1" ] || [ "${DOWNLOAD_MODELS}" = "1" ]; then
  INITIAL_STRICT=1
fi

run_preflight "${STAMP}" "${INITIAL_REQUIRE_MODELS}" "${INITIAL_STRICT}"

if [ "${DOWNLOAD_MODELS}" = "1" ]; then
  MODEL_ROOT="${MODEL_ROOT}" bash scripts/download_models.sh 2>&1 | tee "${LOG_DIR}/p01_download_models_${STAMP}.log"
  run_preflight "${STAMP}_post_download" "1" "1"
fi

SUITE_ARGS=(--cases P01 --log-dir "${LOG_DIR}" --result-dir "${RESULT_DIR}")
if [ "${RERUN}" = "1" ]; then
  SUITE_ARGS+=(--rerun)
fi

"${PYTHON_BIN}" -m backend.experiment_suite "${SUITE_ARGS[@]}" --format shell \
  | tee "outputs/reports/p01_smoke_plan_${STAMP}.sh"

if [ "${EXECUTE}" = "1" ]; then
  "${PYTHON_BIN}" -m backend.experiment_suite "${SUITE_ARGS[@]}" --execute 2>&1 \
    | tee "${LOG_DIR}/p01_smoke_execute_${STAMP}.log"
fi

"${PYTHON_BIN}" -m backend.experiment_results --log-dir "${LOG_DIR}" --format markdown \
  --output "outputs/reports/p01_experiment_results_${STAMP}.md"
"${PYTHON_BIN}" -m backend.mobile_video_check --log-dir "${LOG_DIR}" --cases P01 --format markdown \
  --output "outputs/reports/p01_mobile_video_check_${STAMP}.md"
"${PYTHON_BIN}" -m backend.feasibility_decision --log-dir "${LOG_DIR}" --format markdown \
  | tee "outputs/reports/p01_feasibility_decision_${STAMP}.md"
"${PYTHON_BIN}" -m backend.final_report --log-dir "${LOG_DIR}" --format markdown \
  | tee "outputs/reports/p01_final_report_${STAMP}.md"

echo "p01_preflight_json=${LOG_DIR}/p01_preflight_${STAMP}.json"
echo "p01_preflight_report=outputs/reports/p01_preflight_${STAMP}.md"
if [ "${DOWNLOAD_MODELS}" = "1" ]; then
  echo "p01_post_download_preflight_json=${LOG_DIR}/p01_preflight_${STAMP}_post_download.json"
  echo "p01_post_download_preflight_report=outputs/reports/p01_preflight_${STAMP}_post_download.md"
fi
echo "p01_smoke_plan=outputs/reports/p01_smoke_plan_${STAMP}.sh"
if [ "${EXECUTE}" = "1" ]; then
  echo "p01_execute_log=${LOG_DIR}/p01_smoke_execute_${STAMP}.log"
fi
echo "p01_experiment_report=outputs/reports/p01_experiment_results_${STAMP}.md"
echo "p01_mobile_video_report=outputs/reports/p01_mobile_video_check_${STAMP}.md"
echo "p01_feasibility_report=outputs/reports/p01_feasibility_decision_${STAMP}.md"
echo "p01_final_report=outputs/reports/p01_final_report_${STAMP}.md"
