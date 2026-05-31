#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="python"
  echo "Using fallback python from PATH because .venv/bin/python is not available."
fi

if [ "$#" -gt 0 ]; then
  "$PYTHON" -m pytest "$@" -q
else
  "$PYTHON" -m pytest tests/acceptance -q
fi
