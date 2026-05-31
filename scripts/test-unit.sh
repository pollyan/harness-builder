#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

. scripts/lib-test-env.sh

if [ "$#" -gt 0 ] && [[ "$1" != -* ]]; then
  hb_run_pytest "$@"
else
  hb_run_pytest tests/unit "$@"
fi
