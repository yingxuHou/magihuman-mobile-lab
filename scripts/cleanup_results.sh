#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${DATA_DIR:-api_data}"
TTL_SECONDS="${TTL_SECONDS:-86400}"

python -m backend.retention --data-dir "${DATA_DIR}" --ttl-seconds "${TTL_SECONDS}"

