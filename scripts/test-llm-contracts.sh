#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

. scripts/lib-test-env.sh

if [ "$#" -gt 0 ] && [[ "$1" != -* ]]; then
  hb_run_pytest "$@"
else
  hb_run_pytest \
    tests/unit/test_llm_scan_analyzer.py \
    tests/unit/test_scan_reconciler.py \
    tests/unit/test_llm_maturity_reviewer.py \
    tests/unit/test_llm_asset_candidate_generator.py \
    tests/unit/test_llm_workflow_router.py \
    tests/unit/test_llm_experience_summarizer.py \
    tests/unit/test_prompt_assets.py \
    tests/unit/test_schema_contracts.py \
    "$@"
fi
