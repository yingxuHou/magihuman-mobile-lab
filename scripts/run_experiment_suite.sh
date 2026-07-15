#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="${LOG_DIR:-logs}"
RESULT_DIR="${RESULT_DIR:-outputs/experiment-results}"
FORMAT="${FORMAT:-shell}"

python -m backend.experiment_suite \
  --log-dir "$LOG_DIR" \
  --result-dir "$RESULT_DIR" \
  --format "$FORMAT" \
  "$@"
