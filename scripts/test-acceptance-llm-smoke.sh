#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

scripts/test-acceptance.sh tests/acceptance/test_real_llm_scan.py "$@"
