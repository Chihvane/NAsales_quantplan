#!/usr/bin/env bash

if [ -n "${BASH_SOURCE[0]:-}" ]; then
  SCRIPT_PATH="${BASH_SOURCE[0]}"
elif [ -n "${ZSH_VERSION:-}" ]; then
  SCRIPT_PATH="${(%):-%N}"
else
  SCRIPT_PATH="$0"
fi

PROJECT_ROOT="$(cd "$(dirname "${SCRIPT_PATH}")/.." && pwd)"

export PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
export MPLCONFIGDIR="${PROJECT_ROOT}/.cache/matplotlib"
export PATH="${HOME}/Library/Python/3.9/bin:${PATH}"

mkdir -p "${MPLCONFIGDIR}"
