#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 PATH_TO_GPU_EVIDENCE_TAR_GZ [backend.gpu_evidence_import_workflow args...]" >&2
  exit 2
fi

ARCHIVE_PATH="$1"
shift

python -m backend.gpu_evidence_import_workflow --archive "${ARCHIVE_PATH}" "$@"
