#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${DATA_DIR:-api_data}"
OUTPUT_DIR="${OUTPUT_DIR:-outputs/api-results}"

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 '<command template>'" >&2
  exit 2
fi

python -m backend.worker --data-dir "${DATA_DIR}" --output-dir "${OUTPUT_DIR}" --command "$1"

