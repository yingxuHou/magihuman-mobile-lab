#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

STAMP="$(date '+%Y%m%d_%H%M%S')"
SUMMARY_PATH="${SUMMARY_PATH:-outputs/reports/gpu_reproduction_workflow_${STAMP}.md}"

UPSTREAM_DRIFT_AUDIT="${UPSTREAM_DRIFT_AUDIT:-1}"
PREPARE_SOURCES="${PREPARE_SOURCES:-1}"
INSTALL_MAGICOMPILER="${INSTALL_MAGICOMPILER:-1}"
RUN_P01="${RUN_P01:-1}"
RUN_FULL="${RUN_FULL:-1}"
PACKAGE_EVIDENCE="${PACKAGE_EVIDENCE:-1}"
P01_DOWNLOAD_MODELS="${P01_DOWNLOAD_MODELS:-1}"
FULL_DOWNLOAD_MODELS="${FULL_DOWNLOAD_MODELS:-1}"
INCLUDE_OPTIONAL="${INCLUDE_OPTIONAL:-0}"

mkdir -p logs outputs/reports

{
  echo "# GPU Reproduction Workflow"
  echo ""
  echo "- Timestamp: \`${STAMP}\`"
  echo "- Run P01: ${RUN_P01}"
  echo "- Run full suite: ${RUN_FULL}"
  echo "- Package evidence: ${PACKAGE_EVIDENCE}"
  echo "- P01 download models: ${P01_DOWNLOAD_MODELS}"
  echo "- Full-suite download models: ${FULL_DOWNLOAD_MODELS}"
  echo "- Include optional cases: ${INCLUDE_OPTIONAL}"
  echo ""
  echo "## Steps"
} > "${SUMMARY_PATH}"

run_step() {
  local label="$1"
  shift

  echo "== ${label} =="
  echo "- ${label}: started" >> "${SUMMARY_PATH}"
  if "$@"; then
    echo "- ${label}: completed" >> "${SUMMARY_PATH}"
  else
    local rc="$?"
    echo "- ${label}: failed with exit code ${rc}" >> "${SUMMARY_PATH}"
    echo "failed_step=${label}"
    echo "summary=${SUMMARY_PATH}"
    exit "${rc}"
  fi
}

if [ "${UPSTREAM_DRIFT_AUDIT}" = "1" ]; then
  run_step "upstream drift audit JSON" \
    python -m backend.upstream_drift_audit --format json --output "logs/gpu_workflow_upstream_drift_${STAMP}.json" --strict
  run_step "upstream drift audit report" \
    python -m backend.upstream_drift_audit --format markdown --output "outputs/reports/gpu_workflow_upstream_drift_${STAMP}.md" --strict
fi

if [ "${PREPARE_SOURCES}" = "1" ]; then
  run_step "prepare locked sources" \
    env INSTALL_MAGICOMPILER="${INSTALL_MAGICOMPILER}" bash scripts/prepare_sources.sh
fi

if [ "${RUN_P01}" = "1" ]; then
  run_step "P01 smoke pipeline" \
    env PREPARE_SOURCES=0 INSTALL_MAGICOMPILER="${INSTALL_MAGICOMPILER}" DOWNLOAD_MODELS="${P01_DOWNLOAD_MODELS}" EXECUTE=1 MODEL_PROFILE=p01 bash scripts/run_p01_smoke_pipeline.sh
fi

if [ "${RUN_FULL}" = "1" ]; then
  run_step "required suite pipeline" \
    env PREPARE_SOURCES=0 INSTALL_MAGICOMPILER="${INSTALL_MAGICOMPILER}" DOWNLOAD_MODELS="${FULL_DOWNLOAD_MODELS}" EXECUTE=1 MODEL_PROFILE=required_suite INCLUDE_OPTIONAL="${INCLUDE_OPTIONAL}" bash scripts/gpu_reproduction_pipeline.sh
fi

if [ "${PACKAGE_EVIDENCE}" = "1" ]; then
  run_step "package GPU evidence" \
    bash scripts/package_gpu_evidence.sh
fi

{
  echo ""
  echo "## Expected Reports"
  echo ""
  echo "- P01 acceptance: \`outputs/reports/p01_acceptance_*.md\`"
  echo "- Required-suite acceptance: \`outputs/reports/required_suite_acceptance_*.md\`"
  echo "- Evidence package manifest: \`outputs/gpu-evidence-*/evidence-manifest.md\`"
  echo ""
  echo "Workflow completed."
} >> "${SUMMARY_PATH}"

echo "workflow_summary=${SUMMARY_PATH}"
