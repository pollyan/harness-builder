# Hard Gate 置信度降级 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 `init` 生成低置信度 hard gate，导致 freshly generated Harness 无法通过 benchmark 的契约不一致问题。

**Architecture:** 在扫描调和阶段统一执行 gate eligibility。`benchmark` 保持严格验收，不为生成阶段的错误放宽规则；Markdown 与 README 只记录稳定规则。

**Tech Stack:** Python 3.11+、Pydantic、pytest、Typer CLI。

---

### Task 1: 回归测试

**Files:**
- Modify: `tests/unit/test_scan_reconciler.py`

- [ ] **Step 1: 写失败测试**

新增 `test_reconcile_downgrades_low_confidence_hard_gate_even_with_source_evidence`，构造 `source=pom.xml` 且 `confidence=low` 的 hard gate，期望输出 gate 为 `soft`，并存在 `command_low_confidence_hard_gate` warning。

- [ ] **Step 2: 运行测试确认失败**

Run: `.venv/bin/python -m pytest tests/unit/test_scan_reconciler.py::test_reconcile_downgrades_low_confidence_hard_gate_even_with_source_evidence -q`

Expected: FAIL，因为当前实现会保留 `gate=hard`。

### Task 2: 调和阶段降级

**Files:**
- Modify: `src/harness_builder_agent/tools/scan_reconciler.py`

- [ ] **Step 1: 最小实现**

在 `_command_from_candidate()` 中，当 `candidate.gate == "hard"` 且 `candidate.confidence == "low"` 时，把 gate 改为 `soft`，保留 confidence 为 `low`，并添加 `command_low_confidence_hard_gate` warning。

- [ ] **Step 2: 运行 targeted 测试**

Run: `.venv/bin/python -m pytest tests/unit/test_scan_reconciler.py -q`

Expected: PASS。

### Task 3: 文档更新

**Files:**
- Modify: `README.md`
- Modify: `docs/engineering/sensor-and-gate-rules.md`
- Modify: `docs/engineering/llm-contracts.md`

- [ ] **Step 1: 更新用户文档**

在 README 的 `benchmark` / `init` 说明中补充：低置信度验证命令会作为 soft gate 或人工确认项保留，不能自动成为 hard gate。

- [ ] **Step 2: 更新工程规则**

在 Sensor 与 LLM 契约中补充同一规则，避免后续 prompt、reconciler 或 writer 改动重新引入低置信度 hard gate。

### Task 4: 验证

**Files:**
- No production files beyond previous tasks.

- [ ] **Step 1: targeted 测试**

Run: `.venv/bin/python -m pytest tests/unit/test_scan_reconciler.py tests/integration/test_benchmark_command.py::test_benchmark_degrades_command_reliability_for_low_confidence_hard_gate -q`

Expected: PASS。

- [ ] **Step 2: 快速回归**

Run: `scripts/test-fast.sh`

Expected: PASS。

- [ ] **Step 3: 真实 smoke**

在临时目录复制 `tests/fixtures/mini-spring-boot` 且排除旧 `.ai`，运行真实 DeepSeek `init --non-interactive` 和 `benchmark --profile java-spring`。Expected: 如果 LLM 仍输出低置信度测试命令，该命令应被降级为 soft，不再触发 `content:hard-gate-command-evidence` 的 low-confidence 失败。
