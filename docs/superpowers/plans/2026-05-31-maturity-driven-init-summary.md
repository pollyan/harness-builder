# Maturity Driven Init Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make first-run `init` finish with a maturity-driven summary file and concise CLI next-step guidance.

**Architecture:** Add a focused init summary writer/renderer around existing `MaturityReport`, wire it into report asset generation and CLI completion output, then extend benchmark and integration tests to treat the summary as part of the init contract.

**Tech Stack:** Python, Typer, Pydantic, PyYAML, pytest.

---

### Task 1: Failing Init Summary Tests

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`
- Modify: `tests/e2e/test_fixture_end_to_end.py`
- Modify: `tests/integration/test_benchmark_command.py`

- [x] Add assertions that `.ai/init-summary.md` exists after init.
- [x] Assert stable sections: `## 当前成熟度`、`## 主要阻断项`、`## 建议下一步`、`## 推荐入口文件`、`## 本次未执行的事项`.
- [x] Assert CLI output includes `当前成熟度` and `.ai/init-summary.md`.
- [x] Assert benchmark includes and passes `exists:init-summary.md` and `content:init-summary`.

### Task 2: Init Summary Writer And CLI Renderer

**Files:**
- Create: `src/harness_builder_agent/tools/init_summary.py`
- Modify: `src/harness_builder_agent/tools/asset_writers/reports.py`
- Modify: `src/harness_builder_agent/cli.py`

- [x] Implement `build_init_summary_markdown(score: MaturityReport) -> str`.
- [x] Implement `render_init_completion_message(ai: Path) -> str` that validates `maturity-score.yaml`.
- [x] Write `.ai/init-summary.md` from `write_report_assets` and record it in trace as `init_summary`.
- [x] Print the rendered summary after both guided and non-interactive init.

### Task 3: Benchmark Contract

**Files:**
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/integration/test_benchmark_command.py`

- [x] Add `init-summary.md` to required files.
- [x] Add `_init_summary_check` validating key sections, `.ai/maturity-report.md`, `.ai/human-input-needed.md`, and no Runtime task-run boundary language.

### Task 4: Docs And Gate

**Files:**
- Modify: `README.md`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/engineering/testing-strategy.md`
- Modify: `docs/evolution-log.md`
- Modify: `docs/todos/maturity-driven-init-wizard.md`

- [x] Document `.ai/init-summary.md` as the first-run maturity-driven completion entrypoint.
- [x] Mark this as the first slice of the larger init wizard todo, leaving existing-Harness maintenance open.
- [x] Run targeted tests.
- [x] Run `scripts/test-fast.sh`.
- [ ] Commit locally.
