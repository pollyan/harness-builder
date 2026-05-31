# Runtime 运行证据成熟度门禁 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让成熟度评估在宿主 Runtime 已提供 task-run 证据时进入可验证的 L3 语义，并在 Runtime sensor unresolved 时保持 L2 ceiling。

**Architecture:** 复用现有 `summarize_runtime_task_runs(ai)`，在 `maturity_model.py` 中集中计算 Runtime evidence summary，再驱动 workflow、repair_loop、observability、governance 和 overall level。schema 不变，只调整成熟度报告字段值、evidence 和 blockers。

**Tech Stack:** Python、Pydantic、PyYAML、pytest。

---

### Task 1: Runtime 证据驱动的成熟度单测

**Files:**
- Modify: `tests/unit/test_maturity_model.py`

- [ ] **Step 1: 添加 RED 测试 helper**

在 `tests/unit/test_maturity_model.py` 中添加 `_write_runtime_task_run()` helper，结构复用 Runtime task-run 契约：

```python
def _write_runtime_task_run(ai: Path, task_id: str = "task-1", sensor_status: str = "passed", repair_attempts: int = 0) -> None:
    run = ai / "task-runs" / task_id
    _write_yaml(
        run / "harness-map.yaml",
        {"schema_version": "1.0", "task_id": task_id, "task_type": "bugfix", "selected_workflow": "bugfix"},
    )
    _write_yaml(
        run / "sensor-report.yaml",
        {
            "schema_version": "1.0",
            "task_id": task_id,
            "task": "Fix checkout bug",
            "sensor_results": [
                {
                    "id": "pytest",
                    "command": "pytest",
                    "status": sensor_status,
                    "exit_code": 0 if sensor_status == "passed" else 1,
                    "duration_seconds": 1.0,
                    "summary": f"pytest {sensor_status}",
                }
            ],
        },
    )
    _write_yaml(
        run / "runtime-summary.yaml",
        {
            "schema_version": "1.0",
            "task_id": task_id,
            "selected_workflow": "bugfix",
            "status": "completed" if sensor_status == "passed" else "completed_with_sensor_failures",
            "sensor_status": sensor_status,
            "repair_attempts": repair_attempts,
            "unresolved_sensor_count": 0 if sensor_status == "passed" else 1,
            "risk_count": 1,
            "summary": "Runtime captured outcome.",
        },
    )
    (run / "decision-log.md").write_text("# Decision Log\n\nReviewed routing and sensor outcome.\n", encoding="utf-8")
    (run / "handoff-summary.md").write_text("# Handoff Summary\n\nTask completed with runtime evidence.\n", encoding="utf-8")
```

- [ ] **Step 2: 添加 passed Runtime L3 测试**

```python
def test_runtime_passed_task_run_lifts_workflow_observability_and_overall_to_l3(tmp_path: Path):
    ai = tmp_path / ".ai"
    (ai / "guides").mkdir(parents=True)
    (ai / "guides" / "project-context.md").write_text("# Project Context\n\n## 当前项目事实\n\nReady.\n", encoding="utf-8")
    for skill in ("lightweight", "bugfix", "standard"):
        (ai / "skills" / skill).mkdir(parents=True)
        (ai / "skills" / skill / "SKILL.md").write_text(f"# {skill}\n", encoding="utf-8")
    (ai / "runs" / "init-1").mkdir(parents=True)
    _write_runtime_task_run(ai, sensor_status="passed", repair_attempts=1)

    report = build_maturity_report(ai=ai, inventory=_inventory(), commands=CommandCatalog(commands=[{"id": "test", "command": "pytest", "type": "test", "gate": "hard", "source": "package", "confidence": "high"}]), config=HarnessConfig.default())

    assert report.overall_level == "L3"
    assert report.dimensions["workflow"].level == "L3"
    assert report.dimensions["observability"].level == "L2"
    assert report.dimensions["governance_auditability"].level == "L2"
    assert report.dimensions["repair_loop"].level == "L2"
    assert any(".ai/task-runs/task-1/" == item.source for item in report.dimensions["workflow"].evidence)
```

- [ ] **Step 3: 添加 failed Runtime ceiling 测试**

```python
def test_runtime_failed_sensor_keeps_overall_below_l3(tmp_path: Path):
    ai = tmp_path / ".ai"
    for skill in ("lightweight", "bugfix", "standard"):
        (ai / "skills" / skill).mkdir(parents=True)
        (ai / "skills" / skill / "SKILL.md").write_text(f"# {skill}\n", encoding="utf-8")
    (ai / "runs" / "init-1").mkdir(parents=True)
    _write_runtime_task_run(ai, sensor_status="failed", repair_attempts=1)

    report = build_maturity_report(ai=ai, inventory=_inventory(), commands=CommandCatalog(commands=[{"id": "test", "command": "pytest", "type": "test", "gate": "hard", "source": "package", "confidence": "high"}]), config=HarnessConfig.default())

    assert report.overall_level == "L2"
    assert report.dimensions["workflow"].level == "L2"
    assert any(blocker.id == "runtime-sensors-unresolved" for blocker in report.dimensions["workflow"].blockers)
```

- [ ] **Step 4: 运行 RED 测试**

Run: `.venv/bin/python -m pytest tests/unit/test_maturity_model.py -q`

Expected: FAIL，至少包括 overall 仍为 L2、repair_loop 仍为 L0 或 workflow blocker 缺失。

### Task 2: 实现 Runtime maturity evidence 语义

**Files:**
- Modify: `src/harness_builder_agent/tools/maturity_model.py`

- [ ] **Step 1: 引入 Runtime summary**

在 `maturity_model.py` 导入：

```python
from harness_builder_agent.schemas.runtime_task_run import RuntimeTaskRunCollectionSummary
from harness_builder_agent.tools.runtime_task_runs import summarize_runtime_task_runs
```

- [ ] **Step 2: 在 build_maturity_report 中集中计算 runtime summary**

```python
runtime_summary = summarize_runtime_task_runs(ai) if ai is not None else RuntimeTaskRunCollectionSummary()
runtime_resolved = runtime_summary.task_run_count > 0 and runtime_summary.failed_sensor_count == 0 and runtime_summary.skipped_sensor_count == 0 and runtime_summary.unresolved_sensor_count == 0
```

将 `runtime_summary` 和 `runtime_resolved` 传入 `_workflow_dimension`、`_repair_loop_dimension`、`_observability_dimension`、`_governance_dimension`、`_overall_level` 和 `_blocking_caps`。

- [ ] **Step 3: 更新 workflow 维度**

规则：

- workflow skill 完整且有 standard escalation，但无 Runtime task-run：L2，blocker `runtime-workflow-not-observed`。
- 有 Runtime task-run 但存在 failed / skipped / unresolved：L2，blocker `runtime-sensors-unresolved`。
- workflow skill 完整、standard escalation 存在、Runtime task-run 全部 resolved：L3。

- [ ] **Step 4: 更新 repair_loop 维度**

规则：

- 无 Runtime task-run：L0。
- 有 Runtime task-run 且 `repair_attempt_count > 0`：L2，evidence 引用 `.ai/task-runs/<task-id>/`。
- 有 Runtime task-run 但无 repair attempts：L1，说明有结果但未观察到 repair loop。

- [ ] **Step 5: 更新 observability / governance 维度**

规则：

- observability：有 generation trace 但无 runtime 为 L1；有 runtime task-run 为 L2。
- governance：有 runtime task-run 为 L2，因为 required files 已保证 decision log 和 handoff 存在；否则保持原 L1 / L0。

- [ ] **Step 6: 更新 overall 与 blocking caps**

规则：

- 无命令：L0。
- workflow 不完整：L1。
- workflow 完整但 runtime evidence 不足或 unresolved：L2。
- workflow 完整、risk routing 存在、runtime resolved：L3。
- L4 不在本轮实现，保留 next level 和 blocker。

- [ ] **Step 7: 运行 GREEN 单测**

Run: `.venv/bin/python -m pytest tests/unit/test_maturity_model.py tests/unit/test_maturity_evidence.py -q`

Expected: PASS。

### Task 3: 文档与演进记录

**Files:**
- Modify: `README.md`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/evolution-log.md`

- [ ] **Step 1: README 补充成熟度语义**

在 Runtime task-run 说明后追加：`assess` 会把合法 task-run 作为成熟度证据；全部 resolved 的 Runtime sensor 结果可支撑 Workflow-bound L3，failed/skipped/unresolved 会作为 blocker。

- [ ] **Step 2: init-workflow 补充 maturity evidence 规则**

在 maturity evidence 段落中说明 runtime_task_run_count 不只进入 evidence pack，还会影响 workflow / observability / governance / repair_loop 维度和 L3 ceiling。

- [ ] **Step 3: evolution-log 追加本轮记录**

在文件顶部新增 `2026-05-31 Runtime 运行证据成熟度门禁`，包含 North Star 模块、Gap Analysis、用户故事、决策、验收、完成内容和 Self-Harness Gate。

- [ ] **Step 4: 运行文档相关快速检查**

Run: `.venv/bin/python -m pytest tests/unit/test_maturity_model.py tests/unit/test_maturity_evidence.py -q`

Expected: PASS。

### Task 4: 最终验证与提交

**Files:**
- All modified files.

- [ ] **Step 1: 运行目标回归**

Run: `.venv/bin/python -m pytest tests/unit/test_maturity_model.py tests/unit/test_maturity_evidence.py tests/integration/test_assess_improve_commands.py tests/integration/test_benchmark_command.py -q`

Expected: PASS。

- [ ] **Step 2: 运行快速回归**

Run: `scripts/test-fast.sh`

Expected: PASS。

- [ ] **Step 3: 提交**

```bash
git add src/harness_builder_agent/tools/maturity_model.py tests/unit/test_maturity_model.py README.md docs/engineering/init-workflow.md docs/evolution-log.md docs/superpowers/specs/2026-05-31-runtime-maturity-gates-design.md docs/superpowers/plans/2026-05-31-runtime-maturity-gates.md
git commit -m "接入 Runtime 运行证据成熟度门禁"
```

