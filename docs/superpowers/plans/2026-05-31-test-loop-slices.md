# Test Loop Slices Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add tested, documented test loop slice scripts and a safe fast regression stamp so goal-mode iterations can run narrower checks without weakening full validation gates.

**Architecture:** Keep shell behavior in small scripts, share Python/stamp logic through `scripts/lib-test-env.sh`, and test the scripts from pytest using subprocess in temporary git repos where needed. Documentation explains slices as development feedback shortcuts, while AGENTS fast/full rules remain authoritative.

**Tech Stack:** Bash, pytest, subprocess, git, Markdown docs.

---

## Files

- Create `tests/unit/test_test_scripts.py`
  - Verifies script syntax, documented entrypoints, and fast stamp behavior.
- Modify `scripts/lib-test-env.sh`
  - Move fast stamp path to `.pytest_cache/harness-builder-test-fast.stamp`.
- Modify `scripts/test-fast.sh`
  - Keep target passthrough and whole-tree stamp behavior.
- Modify `.githooks/pre-commit`
  - Keep duplicate fast skip using the shared helper.
- Add slice scripts under `scripts/`
  - `test-unit.sh`, `test-integration.sh`, `test-guided-init.sh`, `test-llm-contracts.sh`, `test-acceptance-llm-smoke.sh`, `test-acceptance-real-repo.sh`, `test-acceptance-self-improve.sh`.
- Modify docs:
  - `README.md`
  - `docs/engineering/testing-strategy.md`
  - `docs/todos/testing-coverage-and-acceptance-strategy.md`
  - `docs/evolution-log.md`

## Tasks

### Task 1: RED Tests

- [x] Add `tests/unit/test_test_scripts.py` with failing expectations for documented slice scripts and `.pytest_cache` stamp path.
- [x] Run `pytest tests/unit/test_test_scripts.py -q` and confirm the failure is the current `.git` stamp path or missing docs.

### Task 2: Green Script Contract

- [x] Update `scripts/lib-test-env.sh` so `hb_fast_stamp_path` returns `.pytest_cache/harness-builder-test-fast.stamp`.
- [x] Keep target passthrough behavior in `scripts/test-fast.sh`, `scripts/test-unit.sh`, `scripts/test-integration.sh`, `scripts/test-guided-init.sh`, and `scripts/test-llm-contracts.sh`.
- [x] Keep acceptance wrappers as targeted pass-through helpers.
- [x] Run `pytest tests/unit/test_test_scripts.py -q`.

### Task 3: Docs And Verification

- [x] Update README testing section with all slice scripts and full/acceptance boundary language.
- [x] Update `docs/engineering/testing-strategy.md` with slice purpose and stamp semantics.
- [x] Update todo implemented result and evolution log.
- [x] Run targeted shell checks for slice scripts.
- [x] Run `scripts/test-fast.sh`.
- [x] Commit with message `chore: add test loop slice scripts`.
