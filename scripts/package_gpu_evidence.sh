#!/usr/bin/env bash
set -euo pipefail

STAMP="$(date '+%Y%m%d_%H%M%S')"
PACKAGE_DIR="${PACKAGE_DIR:-outputs/gpu-evidence-${STAMP}}"
ARCHIVE_PATH="${ARCHIVE_PATH:-${PACKAGE_DIR}.tar.gz}"

mkdir -p "${PACKAGE_DIR}/logs" "${PACKAGE_DIR}/docs" "${PACKAGE_DIR}/outputs/reports"

if [ -d logs ]; then
  find logs -maxdepth 1 -type f \( \
    -name '*_metrics.json' -o \
    -name '*preflight*.json' -o \
    -name '*model_audit*.json' -o \
    -name '*hf_access*.json' -o \
    -name '*artifact_audit*.json' -o \
    -name '*smoke_plan_audit*.json' -o \
    -name '*download_log_audit*.json' -o \
    -name '*p01_acceptance*.json' -o \
    -name '*required_suite_acceptance*.json' -o \
    -name '*workflow_readiness*.json' \
  \) -exec cp {} "${PACKAGE_DIR}/logs/" \; 2>/dev/null || true
fi

for file in \
  docs/quality-review.json \
  docs/cost-review.json \
  docs/mobile-feasibility-report.md \
  docs/gpu-evidence-import-audit.md \
  docs/p01-smoke-manifest.json \
  docs/p01-smoke-manifest.md; do
  if [ -f "${file}" ]; then
    cp "${file}" "${PACKAGE_DIR}/docs/"
  fi
done

if [ -d outputs/reports ]; then
  find outputs/reports -maxdepth 1 -type f \( -name '*.md' -o -name '*.json' -o -name '*.log' \) \
    -exec cp {} "${PACKAGE_DIR}/outputs/reports/" \; 2>/dev/null || true
fi

python -m backend.evidence_provenance --project-root . --format json \
  --output "${PACKAGE_DIR}/evidence-provenance.json"
python -m backend.evidence_provenance --project-root . --format markdown \
  --output "${PACKAGE_DIR}/evidence-provenance.md"

python -m backend.evidence_package --package-dir "${PACKAGE_DIR}" --format json \
  --output "${PACKAGE_DIR}/evidence-manifest.json" --strict
python -m backend.evidence_package --package-dir "${PACKAGE_DIR}" --format markdown \
  --output "${PACKAGE_DIR}/evidence-manifest.md" --strict

tar -czf "${ARCHIVE_PATH}" -C "$(dirname "${PACKAGE_DIR}")" "$(basename "${PACKAGE_DIR}")"

echo "package_dir=${PACKAGE_DIR}"
echo "archive_path=${ARCHIVE_PATH}"
