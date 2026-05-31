# LLM-Guided Evidence Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let scan use an LLM evidence planner to request additional in-repo files before the final LLM scan proposal is generated.

**Architecture:** Add a small planning schema/prompt/tool before the existing scan analyzer. The planner can only choose paths from the deterministic file index; Python validates the allowlist, reads summaries for requested files, and appends them as structured `llm_requested_files` evidence.

**Tech Stack:** Python, Pydantic, Markdown prompt assets, pytest.

---

## Files

- Create `src/harness_builder_agent/tools/llm_evidence_planner.py`
- Create `src/harness_builder_agent/prompts/llm_evidence_plan_v1.md`
- Modify `src/harness_builder_agent/schemas/scan.py`
- Modify `src/harness_builder_agent/tools/evidence_collector.py`
- Modify `src/harness_builder_agent/tools/scan_repo.py`
- Modify `src/harness_builder_agent/prompts/registry.py`
- Modify `tests/unit/test_llm_evidence_planner.py`
- Modify `tests/unit/test_evidence_collector.py`
- Modify `tests/unit/test_scan_repo.py`
- Modify `tests/unit/test_prompt_assets.py`
- Modify docs: `docs/engineering/llm-contracts.md`, `docs/engineering/architecture.md`, `docs/evolution-log.md`

## Tasks

### Task 1: RED Tests

- [x] Add planner parser tests for valid JSON fence, invalid JSON, schema mismatch, outside path, and unknown in-repo path.
- [x] Add evidence expansion test showing a source file skipped by deterministic source sampling can be added to `llm_requested_files`.
- [x] Add scan repository test showing planner runs before final scan and final scan messages include `llm_requested_files`.
- [x] Update prompt asset tests so prompt inventory is discovered from `prompts/*.md` instead of duplicated in the test.
- [x] Run targeted tests and confirm they fail for missing planner/schema/prompt behavior.

RED verification:

```text
scripts/test-unit.sh tests/unit/test_llm_evidence_planner.py tests/unit/test_evidence_collector.py::test_expand_evidence_adds_llm_requested_file_skipped_by_source_sampling tests/unit/test_scan_repo.py::test_scan_repository_uses_llm_evidence_plan_before_final_scan tests/unit/test_prompt_assets.py -q
ERROR ImportError: cannot import name 'expand_evidence_with_requested_paths'
```

### Task 2: Green Implementation

- [x] Add `LLMEvidencePlan` schema.
- [x] Add prompt registry entry and prompt asset.
- [x] Implement `llm_evidence_planner.py`.
- [x] Add `EvidenceBundle.llm_requested_files` and `expand_evidence_with_requested_paths()`.
- [x] Wire planner into `scan_repository()` with explicit `evidence_planner_caller`.
- [x] Run targeted tests until green.

GREEN verification:

```text
scripts/test-unit.sh tests/unit/test_llm_evidence_planner.py tests/unit/test_evidence_collector.py::test_expand_evidence_adds_llm_requested_file_skipped_by_source_sampling tests/unit/test_scan_repo.py::test_scan_repository_uses_llm_evidence_plan_before_final_scan tests/unit/test_prompt_assets.py -q
13 passed
```

### Task 3: Docs, Gate, Commit

- [x] Update LLM contracts and architecture docs for LLM-guided evidence expansion.
- [x] Update evolution log with gap analysis, user story, decisions, subagent usage, validation, and Self-Harness Gate.
- [x] Run targeted tests.
- [x] Run `scripts/test-fast.sh` before commit.
- [ ] Commit with message `feat: add llm guided evidence expansion`.

Targeted verification:

```text
scripts/test-unit.sh tests/unit/test_llm_evidence_planner.py tests/unit/test_evidence_collector.py tests/unit/test_scan_repo.py tests/unit/test_prompt_assets.py tests/unit/test_llm_scan_analyzer.py tests/unit/test_schema_contracts.py -q
80 passed

scripts/test-fast.sh
259 passed in 13.34s
```
