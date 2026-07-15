#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 CASE_ID [--execute] [--force]" >&2
  exit 2
fi

CASE_ID="$1"
shift

python -m backend.experiment_runner \
  --case "${CASE_ID}" \
  --log-dir "${LOG_DIR:-logs}" \
  --result-dir "${RESULT_DIR:-outputs/experiment-results}" \
  "$@"

