#!/usr/bin/env bash
set -euo pipefail

STAMP="$(date '+%Y%m%d_%H%M%S')"
PACKAGE_DIR="${PACKAGE_DIR:-outputs/gpu-evidence-${STAMP}}"
ARCHIVE_PATH="${ARCHIVE_PATH:-${PACKAGE_DIR}.tar.gz}"

mkdir -p "${PACKAGE_DIR}/logs" "${PACKAGE_DIR}/docs" "${PACKAGE_DIR}/outputs/reports"

find logs -maxdepth 1 -type f -name '*_metrics.json' -exec cp {} "${PACKAGE_DIR}/logs/" \; 2>/dev/null || true

for file in docs/quality-review.json docs/cost-review.json docs/mobile-feasibility-report.md; do
  if [ -f "${file}" ]; then
    cp "${file}" "${PACKAGE_DIR}/docs/"
  fi
done

if [ -d outputs/reports ]; then
  find outputs/reports -maxdepth 1 -type f \( -name '*.md' -o -name '*.json' -o -name '*.log' \) \
    -exec cp {} "${PACKAGE_DIR}/outputs/reports/" \; 2>/dev/null || true
fi

tar -czf "${ARCHIVE_PATH}" -C "$(dirname "${PACKAGE_DIR}")" "$(basename "${PACKAGE_DIR}")"

echo "package_dir=${PACKAGE_DIR}"
echo "archive_path=${ARCHIVE_PATH}"
