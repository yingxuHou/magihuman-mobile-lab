#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8080}"
DATA_DIR="${DATA_DIR:-api_data}"

python -m backend.api_server --host "${HOST}" --port "${PORT}" --data-dir "${DATA_DIR}"

