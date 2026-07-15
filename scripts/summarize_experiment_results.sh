#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="${LOG_DIR:-logs}"
FORMAT="${FORMAT:-markdown}"
OUTPUT="${OUTPUT:-}"
MATRIX="${MATRIX:-}"

ARGS=(python -m backend.experiment_results --log-dir "${LOG_DIR}" --format "${FORMAT}")

if [ "${MATRIX}" != "" ]; then
  ARGS+=(--matrix "${MATRIX}")
fi

if [ "${OUTPUT}" != "" ]; then
  ARGS+=(--output "${OUTPUT}")
fi

"${ARGS[@]}"

