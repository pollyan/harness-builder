#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

target="all"
if [ "$#" -gt 0 ] && [[ "$1" != -* ]]; then
  target="$1"
  shift
fi

case "$target" in
  all)
    scripts/test-acceptance.sh tests/acceptance/test_real_repositories_e2e.py "$@"
    ;;
  ruoyi|java|java-spring)
    scripts/test-acceptance.sh tests/acceptance/test_real_repositories_e2e.py::test_ruoyi_vue_real_repository_with_self_improve "$@"
    ;;
  eshop|dotnet|dotnet-aspnet)
    scripts/test-acceptance.sh tests/acceptance/test_real_repositories_e2e.py::test_eshoponweb_real_repository_end_to_end "$@"
    ;;
  *)
    scripts/test-acceptance.sh "$target" "$@"
    ;;
esac
