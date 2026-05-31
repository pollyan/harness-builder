# 成熟度叙事中文化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 CLI、成熟度报告和 init summary 消费的 `MaturityReport` 用户叙事默认使用中文。

**Architecture:** 在 `maturity_model.py` 源头替换 user-facing string，保留 schema 字段、dimension key 和 blocker id；测试覆盖源头报告、report asset、guided CLI transcript。

**Tech Stack:** Python、Pydantic、pytest、Typer integration tests。

---

### Task 1: 写成熟度源头红灯测试

**Files:**
- Modify: `tests/unit/test_maturity_model.py`

- [ ] 增加 `test_maturity_report_uses_chinese_user_facing_narrative`，构造默认 maturity report，断言不包含 `Guides are structured`、`Bind guides`、`Workflow routing policy exists`，并包含 `Guides 已结构化`、`绑定 Guides`、`Runtime task-run 证据验证 Workflow routing`。
- [ ] 修改 runtime failed sensor 测试，把英文 blocker 断言改为中文，同时保留 blocker id 和 level 断言。
- [ ] 运行目标测试，确认失败来自英文文案未翻译。

### Task 2: 写报告资产红灯测试

**Files:**
- Modify: `tests/unit/test_asset_writer_reports.py`

- [ ] 把 workflow evidence summary 和 next level requirement 的断言改为中文。
- [ ] 断言 `maturity-score.yaml` 不包含 `Workflow routing rules configured` 和 `Validate workflow routing`。
- [ ] 运行目标测试，确认失败来自 `maturity_model.py` 英文输出。

### Task 3: 写 guided CLI 红灯测试

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [ ] 在 guided happy path 的成熟度区块中断言不包含 `Guides are structured`、`Workflow routing policy exists`、`Bind guides to workflow`、`Validate workflow routing`。
- [ ] 断言输出包含 `Guides 已结构化` 和 `用全部 resolved 的 Runtime task-run 证据验证 Workflow routing`。
- [ ] 运行目标测试，确认失败来自 CLI 直接消费英文 maturity report。

### Task 4: 源头中文化实现

**Files:**
- Modify: `src/harness_builder_agent/tools/maturity_model.py`
- Create: `src/harness_builder_agent/tools/maturity_rendering.py`
- Modify: `src/harness_builder_agent/tools/asset_writers/reports.py`
- Modify: `src/harness_builder_agent/tools/assess_maturity.py`

- [ ] 替换所有 user-facing `MaturityEvidence.summary` 英文句。
- [ ] 替换所有 `MaturityBlocker.reason` 英文句。
- [ ] 替换所有 `next_level_requirements` 英文句。
- [ ] 替换 `MaturityBlockingCap.reason` 与 evidence 中的英文说明。
- [ ] 保留 blocker id、dimension key、source path 和 schema 字段不变。
- [ ] 新增 report rendering helper，把维度 key 显示为中文标签并保留机器 key，替换 `evidence:` / `blockers:` 英文展示标签。

### Task 5: 验证、记录和提交

**Files:**
- Modify: `docs/todos/guided-init-ai4se-real-repo-findings.md`
- Modify: `docs/evolution-log.md`
- Create: `docs/superpowers/specs/2026-05-31-maturity-narrative-cn-design.md`
- Create: `docs/superpowers/plans/2026-05-31-maturity-narrative-cn.md`

- [ ] 运行 focused tests：

```bash
.venv/bin/python -m pytest tests/unit/test_maturity_model.py tests/unit/test_asset_writer_reports.py tests/unit/test_init_summary.py tests/integration/test_assess_improve_commands.py::test_assess_generates_maturity_score_from_current_harness tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path -q
```

- [ ] 更新 todo 已完成切片和演进记录。
- [ ] 运行 `scripts/test-fast.sh`。
- [ ] 提交：

```bash
git add src/harness_builder_agent/tools/maturity_model.py src/harness_builder_agent/tools/maturity_rendering.py src/harness_builder_agent/tools/asset_writers/reports.py src/harness_builder_agent/tools/assess_maturity.py tests/unit/test_maturity_model.py tests/unit/test_asset_writer_reports.py tests/integration/test_assess_improve_commands.py tests/integration/test_init_on_fixture_projects.py docs/todos/guided-init-ai4se-real-repo-findings.md docs/evolution-log.md docs/superpowers/specs/2026-05-31-maturity-narrative-cn-design.md docs/superpowers/plans/2026-05-31-maturity-narrative-cn.md
git commit -m "中文化成熟度叙事"
```
