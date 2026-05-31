# Guided Init 启动边界说明 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在首次 guided `init` 进入扫描前展示稳定的中文启动边界说明。

**Architecture:** 在 `interactive_init.py` 中新增一个只负责 CLI 输出的 helper，并在首次生成向导确认继续之前调用。测试通过 integration happy path 验证 transcript 顺序和关键文案，同时确认非交互路径不受影响。

**Tech Stack:** Python、Typer CLI、pytest、CliRunner。

---

### Task 1: 增加 guided init 启动边界说明

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`
- Modify: `src/harness_builder_agent/tools/interactive_init.py`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/evolution-log.md`
- Modify: `docs/todos/maturity-driven-init-wizard.md`

- [ ] **Step 1: Write the failing integration assertions**

在 `tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path` 中，在现有 `assert result.exit_code == 0` 后补充：

```python
    assert "== 启动说明 ==" in result.output
    assert result.output.index("== 启动说明 ==") < result.output.index("继续生成 Harness?")
    assert result.output.index("== 启动说明 ==") < result.output.index("扫描仓库")
    assert "将扫描仓库文件、构建配置、CI、测试、文档和源码样本证据" in result.output
    assert "需要你确认或补充技术栈、模块边界、风险区域、验证命令、团队规则和 Workflow 说明" in result.output
    assert "最终确认写入后将生成 project inventory、command catalog、Guides、Sensors、Workflow Skills、成熟度报告和待确认项" in result.output
    assert "本次会话会记录 generation trace，用于审计取消、失败和完成结果" in result.output
    assert "不会执行 Runtime" in result.output
    assert "不会创建 `.ai/task-runs`" in result.output
    assert "不会默认运行 benchmark" in result.output
    assert "最终输入 `confirm` 前，不会写入或覆盖正式 Harness 资产；trace 只记录本次会话过程" in result.output
```

在 `test_init_non_interactive_generates_existing_assets` 中补充：

```python
    assert "== 启动说明 ==" not in result.output
```

- [ ] **Step 2: Run targeted test and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path tests/integration/test_init_on_fixture_projects.py::test_init_non_interactive_generates_existing_assets -q
```

Expected: guided happy path fails because `== 启动说明 ==` is not in output.

- [ ] **Step 3: Implement the minimal CLI helper**

在 `src/harness_builder_agent/tools/interactive_init.py` 中新增：

```python
def _show_guided_init_startup_boundary() -> None:
    typer.echo("\n== 启动说明 ==")
    typer.echo("- 将扫描仓库文件、构建配置、CI、测试、文档和源码样本证据。")
    typer.echo("- 需要你确认或补充技术栈、模块边界、风险区域、验证命令、团队规则和 Workflow 说明。")
    typer.echo("- 最终确认写入后将生成 project inventory、command catalog、Guides、Sensors、Workflow Skills、成熟度报告和待确认项。")
    typer.echo("- 本次会话会记录 generation trace，用于审计取消、失败和完成结果。")
    typer.echo("- 不会执行 Runtime，不会创建 `.ai/task-runs`，不会默认运行 benchmark。")
    typer.echo("- 在最终输入 `confirm` 前，不会写入或覆盖正式 Harness 资产；trace 只记录本次会话过程。")
```

在 `run_guided_init()` 中，`_handle_existing_harness_entry()` 返回 `None` 后、`typer.confirm("继续生成 Harness?")` 前调用：

```python
    _show_guided_init_startup_boundary()
```

- [ ] **Step 4: Run targeted test and verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path tests/integration/test_init_on_fixture_projects.py::test_init_non_interactive_generates_existing_assets -q
```

Expected: both tests pass.

- [ ] **Step 5: Update docs**

在 `docs/engineering/init-workflow.md` 的 Evidence 收集规则附近补充：首次 guided `init` 在确认继续之前必须输出 `== 启动说明 ==`，说明扫描范围、确认范围、生成资产范围、Runtime / `.ai/task-runs` / benchmark 边界，以及最终 `confirm` 前不写入或覆盖正式 Harness 资产。

在 `docs/todos/maturity-driven-init-wizard.md` 的已完成切片中增加本轮启动边界说明。

在 `docs/evolution-log.md` 顶部增加本轮演进记录，说明 North Star 模块、gap、决策、边界、验收方式和 Self-Harness Gate。

- [ ] **Step 6: Run focused regression**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path tests/integration/test_init_on_fixture_projects.py::test_init_non_interactive_generates_existing_assets -q
```

Expected: tests pass.

- [ ] **Step 7: Run required commit verification**

Run:

```bash
scripts/test-fast.sh
```

Expected: fast regression passes.
