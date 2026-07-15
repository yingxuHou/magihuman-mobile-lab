#!/usr/bin/env bash
set -euo pipefail

MAGIHUMAN_REPO="${MAGIHUMAN_REPO:-https://github.com/GAIR-NLP/daVinci-MagiHuman.git}"
MAGIHUMAN_COMMIT="${MAGIHUMAN_COMMIT:-209209b7086eba2020c5439265221495a8357322}"
MAGICOMPILER_REPO="${MAGICOMPILER_REPO:-https://github.com/SandAI-org/MagiCompiler.git}"
MAGICOMPILER_COMMIT="${MAGICOMPILER_COMMIT:-bfef5bc70226a0c0740e4c551e4f7245a974fb4f}"
INSTALL_MAGICOMPILER="${INSTALL_MAGICOMPILER:-0}"

clone_or_update() {
  local repo="$1"
  local commit="$2"
  local path="$3"

  mkdir -p "$(dirname "${path}")"
  if [ ! -d "${path}/.git" ]; then
    git clone "${repo}" "${path}"
  else
    git -C "${path}" fetch --all --tags
  fi
  git -C "${path}" checkout "${commit}"
  git -C "${path}" rev-parse HEAD
}

clone_or_update "${MAGIHUMAN_REPO}" "${MAGIHUMAN_COMMIT}" "third_party/daVinci-MagiHuman"
clone_or_update "${MAGICOMPILER_REPO}" "${MAGICOMPILER_COMMIT}" "third_party/MagiCompiler"

if [ "${INSTALL_MAGICOMPILER}" = "1" ]; then
  python -m pip install -r third_party/MagiCompiler/requirements.txt
  python -m pip install third_party/MagiCompiler
fi
