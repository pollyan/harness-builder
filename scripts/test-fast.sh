#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

. scripts/lib-test-env.sh

if [ "$#" -gt 0 ]; then
  hb_run_pytest "$@"
else
  hb_run_pytest
  hb_write_fast_stamp
fi
