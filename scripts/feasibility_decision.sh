#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="${LOG_DIR:-logs}"
FORMAT="${FORMAT:-markdown}"
MATRIX_ARG=()

if [[ -n "${MATRIX:-}" ]]; then
  MATRIX_ARG=(--matrix "$MATRIX")
fi

python -m backend.feasibility_decision --log-dir "$LOG_DIR" --format "$FORMAT" "${MATRIX_ARG[@]}"
