#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

git config core.hooksPath .githooks
chmod +x .githooks/pre-commit .githooks/pre-push scripts/check-ci.sh

echo "Git hooks installed from .githooks"

