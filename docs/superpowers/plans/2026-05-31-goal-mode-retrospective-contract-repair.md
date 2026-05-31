# 目标模式回顾与 Workflow Recommendation Benchmark 契约修复实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复真实 `recommend-workflow` 产物无法满足 benchmark workflow recommendation review 章节契约的问题，并记录目标模式回顾补救结论。

**Architecture:** 不放宽 benchmark；调整 producer `recommend_workflow._write_markdown()` 输出稳定章节。Integration 测试从 CLI 生成真实 review artifact，再运行 benchmark 验证同一产物。

**Tech Stack:** Python, Typer CLI, Pydantic schemas, pytest integration tests, Markdown docs.

---

## Files

- Modify `src/harness_builder_agent/tools/recommend_workflow.py`
  - Rename generated Markdown sections to benchmark-required names.
- Modify `tests/integration/test_assess_improve_commands.py`
  - Extend `test_recommend_workflow_writes_review_only_artifacts` to assert required sections and benchmark pass.
- Modify `docs/evolution-log.md`
  - Add retrospective repair entry with Gate conclusion and next candidates.

## Tasks

### Task 1: Red Test

- [ ] Extend `test_recommend_workflow_writes_review_only_artifacts`.
- [ ] Assert Markdown includes:
  - `## Task`
  - `## Recommended Workflow`
  - `## Required Harness Assets`
  - `## Review Boundary`
- [ ] Invoke benchmark on the same generated repo and assert `content:workflow-recommendation-review` passes.

Expected before implementation:

```text
FAILED ... assert '## Task' in markdown
```

### Task 2: Green Implementation

- [ ] In `recommend_workflow._write_markdown`, replace:
  - `## Task Brief` with `## Task`
  - Add `## Recommended Workflow`
  - Combine guides and sensors under `## Required Harness Assets`
  - `## Boundary` with `## Review Boundary`
- [ ] Keep `## Summary`, `## Rationale`, `## Matched Routing Rules`, and `## Evidence Sources`.
- [ ] Keep explicit review-only boundary text.

### Task 3: Docs And Verification

- [ ] Add evolution log entry for this retrospective repair.
- [ ] Run targeted tests:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_recommend_workflow_writes_review_only_artifacts tests/integration/test_benchmark_command.py::test_benchmark_fails_when_workflow_recommendation_markdown_sections_are_missing tests/integration/test_benchmark_command.py::test_benchmark_accepts_valid_workflow_recommendation_review_artifacts -q
```

- [ ] Run `scripts/test-fast.sh` before commit.
