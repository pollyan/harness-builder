#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

. scripts/lib-test-env.sh

if [ "$#" -gt 0 ] && [[ "$1" != -* ]]; then
  hb_run_pytest "$@"
elif [ "$#" -gt 0 ]; then
  hb_run_pytest tests/integration/test_init_on_fixture_projects.py "$@"
else
  hb_run_pytest tests/integration/test_init_on_fixture_projects.py -k guided_init
fi
