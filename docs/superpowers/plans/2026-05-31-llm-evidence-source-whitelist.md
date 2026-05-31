# LLM Evidence Source Whitelist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** As a Harness Maintainer, I can trust review-only LLM artifacts because every cited evidence source is traceable to Builder-provided evidence.

**Architecture:** Add a shared evidence-source allowlist helper used by LLM parsers and benchmark. Parsers require explicit `allowed_evidence_sources`; orchestration functions build the set from structured inputs. Benchmark builds the same set from persisted artifacts and fails optional review checks when unknown `.ai/` evidence paths appear.

**Tech Stack:** Python, Pydantic schemas, pytest unit/integration, Markdown docs.

---

## Files

- Create `src/harness_builder_agent/tools/evidence_sources.py`
  - Build allowlists and validate evidence source lists.
- Modify `src/harness_builder_agent/tools/llm_workflow_router.py`
  - Require `allowed_evidence_sources` in parser and validate recommendation evidence.
- Modify `src/harness_builder_agent/tools/llm_maturity_reviewer.py`
  - Require `allowed_evidence_sources` in parser and validate candidate review evidence.
- Modify `src/harness_builder_agent/tools/llm_asset_candidate_generator.py`
  - Require `allowed_evidence_sources` in parser and validate asset candidate evidence.
- Modify `src/harness_builder_agent/tools/benchmark.py`
  - Build allowed evidence set from persisted schema artifacts and fail unknown sources.
- Modify tests:
  - `tests/unit/test_llm_workflow_router.py`
  - `tests/unit/test_llm_maturity_reviewer.py`
  - `tests/unit/test_llm_asset_candidate_generator.py`
  - `tests/unit/test_llm_experience_summarizer.py` if shared helper affects it.
  - `tests/integration/test_benchmark_command.py`
- Modify docs:
  - `docs/engineering/llm-contracts.md`
  - `docs/engineering/sensor-and-gate-rules.md`
  - `docs/todos/llm-evidence-source-whitelist.md`
  - `docs/evolution-log.md`

## Tasks

### Task 1: RED Tests

- [x] Add workflow router unit test for unknown `.ai/` evidence source.
- [x] Add maturity reviewer unit test for unknown `.ai/` evidence source.
- [x] Add asset candidate unit test for unknown `.ai/` evidence source.
- [x] Update existing parser tests to pass explicit allowlists.
- [x] Add benchmark integration tests for unknown evidence source in workflow recommendation, maturity review, asset candidates, and experience summary.
- [x] Run targeted tests and confirm failures point to missing whitelist behavior.

### Task 2: Green Implementation

- [x] Add `tools/evidence_sources.py` with allowlist builders and validator.
- [x] Wire workflow router orchestration and parser to use the allowlist.
- [x] Wire maturity reviewer orchestration and parser to use the allowlist.
- [x] Wire asset candidate orchestration and parser to use the allowlist.
- [x] Wire benchmark optional review artifact checks to use persisted allowlist.
- [x] Run targeted tests until green.

### Task 3: Docs, Gate, Verification

- [x] Update engineering docs with evidence source whitelist rule.
- [x] Mark the todo implemented or update status.
- [x] Add evolution log entry.
- [x] Run `scripts/test-fast.sh` before commit.
