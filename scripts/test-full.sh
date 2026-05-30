#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

scripts/test-fast.sh
scripts/test-acceptance.sh

