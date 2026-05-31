# First Init Benchmark Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make first `init` completion clearly state whether benchmark validation has run, what its current health status is, and how to run it next.

**Architecture:** Add a read-only benchmark readiness helper to `init_summary.py` that either reports missing benchmark status or validates an existing `BenchmarkReport`. Reuse it in both `init-summary.md` and the CLI completion message.

**Tech Stack:** Python, Pydantic schema validation, Typer CliRunner integration tests, Markdown docs.

---

## Files

- Modify `src/harness_builder_agent/tools/init_summary.py`
  - Import `BenchmarkReport`.
  - Add benchmark readiness helper.
  - Add `## Benchmark 健康度` section to summary.
  - Add benchmark readiness section to completion message.
- Modify `tests/integration/test_init_on_fixture_projects.py`
  - Assert first init summary and CLI output include benchmark readiness.
  - Assert first init still does not create benchmark report.
- Modify `tests/unit/test_init_summary.py` or create it if absent
  - Cover existing benchmark report path through `BenchmarkReport` schema.
- Modify docs:
  - `README.md`
  - `docs/engineering/init-workflow.md`
  - `docs/todos/maturity-driven-init-wizard.md`
  - `docs/evolution-log.md`

## Tasks

### Task 1: RED Tests

- [x] Add / update integration assertions for first init benchmark readiness in Markdown and CLI output.
- [x] Add unit test for existing benchmark report readiness rendering.
- [x] Run targeted tests and confirm failures.

RED verification:

```text
scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_init_generates_ai_assets_for_java_fixture -q
F
```

### Task 2: Green Implementation

- [x] Implement benchmark readiness helper in `init_summary.py`.
- [x] Wire helper into `write_init_summary()` and `render_init_completion_message()`.
- [x] Run targeted tests until green.

GREEN verification:

```text
scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_init_generates_ai_assets_for_java_fixture -q && scripts/test-unit.sh tests/unit/test_init_summary.py -q
.
.
```

### Task 3: Docs, Verification, Commit

- [x] Update README and init workflow docs.
- [x] Update maturity-driven init todo and evolution log.
- [x] Run targeted tests.
- [x] Run `scripts/test-fast.sh`.
- [ ] Commit with message `feat: explain first init benchmark readiness`.

Final verification:

```text
scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_init_generates_ai_assets_for_java_fixture -q
.

scripts/test-unit.sh tests/unit/test_init_summary.py -q
.

scripts/test-integration.sh tests/integration/test_benchmark_command.py::test_benchmark_generates_report_for_java_fixture -q
.

scripts/test-fast.sh
250 passed in 13.41s
```
