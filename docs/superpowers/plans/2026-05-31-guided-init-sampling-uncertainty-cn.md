# Guided Init 采样不确定性中文化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让首次 guided `init` 用中文解释 source sampling / skipped files 覆盖不足，并保留可审计 metadata。

**Architecture:** 在 evidence collector 中补充 warning detail；在 interactive init 的不确定性区块增加 warning 格式化 helper，把稳定机器 warning 翻译为面向用户的 CLI 文案。保持 scan metadata 与现有 schema 兼容。

**Tech Stack:** Python、Typer CLI、Pydantic schema、pytest integration / unit tests。

---

### Task 1: 测试 sampling warning 的 metadata detail

**Files:**
- Modify: `tests/unit/test_evidence_collector.py`
- Modify: `src/harness_builder_agent/tools/evidence_collector.py`

- [ ] **Step 1: Write the failing test**

在 `tests/unit/test_evidence_collector.py` 的大仓库 coverage 测试中，断言 `source_sampling_truncated` warning 包含 `bucket`、`selected_count`、`skipped_count` 和 `total_count`。

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_evidence_collector.py::test_collect_evidence_records_bucket_coverage_for_large_source_sets -q`

Expected: FAIL，因为 warning 暂时没有 `skipped_count` 等 detail。

- [ ] **Step 3: Write minimal implementation**

在 `evidence_collector._coverage()` 创建 warning 时补充：

```python
"total_count": total,
"selected_count": len(selected),
"skipped_count": skipped,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/test_evidence_collector.py::test_collect_evidence_records_bucket_coverage_for_large_source_sets -q`

Expected: PASS。

### Task 2: 测试 guided CLI 中文化 sampling warning

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`
- Modify: `src/harness_builder_agent/tools/interactive_init.py`

- [ ] **Step 1: Write the failing integration assertion**

在 `test_guided_init_groups_scan_risks_uncertainties_and_validation_gaps` 的 fake inventory 中加入 `source_sampling_truncated` warning 和 `scan_metadata.coverage.bucket_coverage`，断言输出包含中文抽样覆盖不足说明，且不包含 `source:.py skipped 73 files`。

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_groups_scan_risks_uncertainties_and_validation_gaps -q`

Expected: FAIL，因为当前 CLI 直接输出 raw warning message。

- [ ] **Step 3: Write minimal implementation**

新增 `_format_scan_warning_for_cli()`、`_coverage_bucket_stats()` 和 `_source_bucket_label()`，并让 `_uncertainty_attention_lines()` 使用格式化结果。

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_groups_scan_risks_uncertainties_and_validation_gaps -q`

Expected: PASS。

### Task 3: 验证相关测试与记录

**Files:**
- Modify: `docs/todos/guided-init-ai4se-real-repo-findings.md`
- Modify: `docs/evolution-log.md`

- [ ] **Step 1: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_evidence_collector.py tests/integration/test_init_on_fixture_projects.py::test_guided_init_groups_scan_risks_uncertainties_and_validation_gaps -q
```

Expected: PASS。

- [ ] **Step 2: Update docs**

在 todo 状态区追加已完成切片，说明 skipped / sampled 中文化已完成，剩余高风险突出、多栈建模、成熟度英文和 LLM-planned deep scan 继续 open。向 `docs/evolution-log.md` 顶部追加本轮记录。

- [ ] **Step 3: Run commit pre-check**

Run: `scripts/test-fast.sh`

Expected: PASS。

- [ ] **Step 4: Commit locally**

Run:

```bash
git add src/harness_builder_agent/tools/evidence_collector.py src/harness_builder_agent/tools/interactive_init.py tests/unit/test_evidence_collector.py tests/integration/test_init_on_fixture_projects.py docs/todos/guided-init-ai4se-real-repo-findings.md docs/evolution-log.md docs/superpowers/specs/2026-05-31-guided-init-sampling-uncertainty-cn-design.md docs/superpowers/plans/2026-05-31-guided-init-sampling-uncertainty-cn.md
git commit -m "中文化init采样覆盖不足说明"
```

Expected: 本地 commit 创建成功，不 push。

## Self-Review

- Spec 覆盖：metadata detail、CLI 中文化、非目标和测试层级均有任务覆盖。
- Placeholder scan：无 TBD / TODO / implement later。
- Type consistency：不新增 schema 字段；warning detail 仍使用 `dict[str, Any]` 兼容现有 `EvidenceCoverage.warnings`。
