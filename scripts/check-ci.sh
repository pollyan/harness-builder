#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

branch="$(git branch --show-current)"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI 'gh' is required to check CI status." >&2
  exit 1
fi

echo "Checking latest GitHub Actions run for branch: ${branch}"

run_id="$(gh run list --branch "$branch" --workflow Tests --limit 1 --json databaseId --jq '.[0].databaseId')"

if [ -z "$run_id" ] || [ "$run_id" = "null" ]; then
  echo "No GitHub Actions run found for branch: ${branch}" >&2
  exit 1
fi

gh run watch "$run_id" --exit-status

