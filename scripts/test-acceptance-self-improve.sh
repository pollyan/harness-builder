#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

scripts/test-acceptance.sh tests/acceptance/test_real_repositories_e2e.py::test_ruoyi_vue_real_repository_with_self_improve "$@"
