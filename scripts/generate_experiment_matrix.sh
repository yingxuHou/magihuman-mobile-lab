#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${OUTPUT:-run_configs/experiment_matrix.json}"
FORMAT="${FORMAT:-json}"

python -m backend.experiment_matrix --output "${OUTPUT}" --format "${FORMAT}"

