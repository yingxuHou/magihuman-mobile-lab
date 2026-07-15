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
HF_ACCESS_AUDIT="${HF_ACCESS_AUDIT:-1}"
PREPARE_SOURCES="${PREPARE_SOURCES:-1}"
INCLUDE_OPTIONAL="${INCLUDE_OPTIONAL:-0}"
QUALITY_REVIEW="${QUALITY_REVIEW:-}"
COST_REVIEW="${COST_REVIEW:-}"
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

  "${PYTHON_BIN}" "${args[@]}" --format json --output "${LOG_DIR}/gpu_preflight_${suffix}.json"
  "${PYTHON_BIN}" "${args[@]}" --format markdown --output "outputs/reports/gpu_preflight_${suffix}.md"
}

run_model_audit() {
  local suffix="$1"
  local strict="$2"
  local args=(-m backend.model_audit --model-root "${MODEL_ROOT}" --profile required_suite)

  if [ "${strict}" = "1" ]; then
    args+=(--strict)
  fi

  "${PYTHON_BIN}" "${args[@]}" --format json --output "${LOG_DIR}/model_audit_${suffix}.json"
  "${PYTHON_BIN}" "${args[@]}" --format markdown --output "outputs/reports/model_audit_${suffix}.md"
}

run_hf_access_audit() {
  local suffix="$1"
  local args=(-m backend.hf_access_audit --profile required_suite)

  "${PYTHON_BIN}" "${args[@]}" --format markdown --output "outputs/reports/hf_access_${suffix}.md"
  "${PYTHON_BIN}" "${args[@]}" --format json --output "${LOG_DIR}/hf_access_${suffix}.json" --strict
}

if [ "${PREPARE_SOURCES}" = "1" ]; then
  bash scripts/prepare_sources.sh 2>&1 | tee "${LOG_DIR}/prepare_sources_${STAMP}.log"
fi

INITIAL_REQUIRE_MODELS=0
if [ "${EXECUTE}" = "1" ] && [ "${DOWNLOAD_MODELS}" != "1" ]; then
  INITIAL_REQUIRE_MODELS=1
fi

INITIAL_STRICT=0
if [ "${EXECUTE}" = "1" ] || [ "${DOWNLOAD_MODELS}" = "1" ]; then
  INITIAL_STRICT=1
fi

INITIAL_MODEL_AUDIT_STRICT=0
if [ "${EXECUTE}" = "1" ] && [ "${DOWNLOAD_MODELS}" != "1" ]; then
  INITIAL_MODEL_AUDIT_STRICT=1
fi

run_preflight "${STAMP}" "${INITIAL_REQUIRE_MODELS}" "${INITIAL_STRICT}"
run_model_audit "${STAMP}" "${INITIAL_MODEL_AUDIT_STRICT}"

if [ "${DOWNLOAD_MODELS}" = "1" ] && [ "${HF_ACCESS_AUDIT}" = "1" ]; then
  run_hf_access_audit "${STAMP}"
fi

if [ "${DOWNLOAD_MODELS}" = "1" ]; then
  MODEL_PROFILE="${MODEL_PROFILE:-required_suite}" MODEL_ROOT="${MODEL_ROOT}" bash scripts/download_models.sh 2>&1 | tee "${LOG_DIR}/download_models_${STAMP}.log"
  run_preflight "${STAMP}_post_download" "1" "1"
  run_model_audit "${STAMP}_post_download" "1"
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
"${PYTHON_BIN}" -m backend.mobile_video_check --log-dir "${LOG_DIR}" --format markdown \
  --output "outputs/reports/mobile_video_check_${STAMP}.md"
FEASIBILITY_ARGS=(-m backend.feasibility_decision --log-dir "${LOG_DIR}" --format markdown)
if [ "${QUALITY_REVIEW}" != "" ]; then
  FEASIBILITY_ARGS+=(--quality-review "${QUALITY_REVIEW}")
fi
if [ "${COST_REVIEW}" != "" ]; then
  FEASIBILITY_ARGS+=(--cost-review "${COST_REVIEW}")
fi
"${PYTHON_BIN}" "${FEASIBILITY_ARGS[@]}" | tee "outputs/reports/feasibility_decision_${STAMP}.md"

FINAL_REPORT_ARGS=(-m backend.final_report --log-dir "${LOG_DIR}" --format markdown)
if [ "${QUALITY_REVIEW}" != "" ]; then
  FINAL_REPORT_ARGS+=(--quality-review "${QUALITY_REVIEW}")
fi
if [ "${COST_REVIEW}" != "" ]; then
  FINAL_REPORT_ARGS+=(--cost-review "${COST_REVIEW}")
fi
"${PYTHON_BIN}" "${FINAL_REPORT_ARGS[@]}" | tee "outputs/reports/final_report_${STAMP}.md"

echo "preflight_json=${LOG_DIR}/gpu_preflight_${STAMP}.json"
echo "preflight_report=outputs/reports/gpu_preflight_${STAMP}.md"
echo "model_audit_json=${LOG_DIR}/model_audit_${STAMP}.json"
echo "model_audit_report=outputs/reports/model_audit_${STAMP}.md"
if [ "${PREPARE_SOURCES}" = "1" ]; then
  echo "prepare_sources_log=${LOG_DIR}/prepare_sources_${STAMP}.log"
fi
if [ "${DOWNLOAD_MODELS}" = "1" ]; then
  if [ "${HF_ACCESS_AUDIT}" = "1" ]; then
    echo "hf_access_json=${LOG_DIR}/hf_access_${STAMP}.json"
    echo "hf_access_report=outputs/reports/hf_access_${STAMP}.md"
  fi
  echo "post_download_preflight_json=${LOG_DIR}/gpu_preflight_${STAMP}_post_download.json"
  echo "post_download_preflight_report=outputs/reports/gpu_preflight_${STAMP}_post_download.md"
  echo "post_download_model_audit_json=${LOG_DIR}/model_audit_${STAMP}_post_download.json"
  echo "post_download_model_audit_report=outputs/reports/model_audit_${STAMP}_post_download.md"
fi
echo "experiment_report=outputs/reports/experiment_results_${STAMP}.md"
echo "mobile_video_report=outputs/reports/mobile_video_check_${STAMP}.md"
echo "feasibility_report=outputs/reports/feasibility_decision_${STAMP}.md"
echo "final_report=outputs/reports/final_report_${STAMP}.md"
