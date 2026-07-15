#!/usr/bin/env bash
set -euo pipefail

python -m backend.model_audit "$@"
