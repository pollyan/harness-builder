# Guided Init 扫描进度反馈 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让首次 guided `init` 在扫描开始、扫描完成和扫描失败时提供稳定、可测试的 CLI 反馈。

**Architecture:** 只在 `interactive_init.py` 的 guided 分支增加渲染函数和显式失败边界；`scan_repository()`、非交互 init、产物写入和 LLM contract 不变。测试放在现有 guided init integration 文件中，覆盖成功路径顺序和扫描失败路径。

**Tech Stack:** Python、Typer、pytest、Typer `CliRunner`、现有 mock scan fixture。

---

### Task 1: 写 RED 测试

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [ ] **Step 1: 扩展 happy path 顺序断言**

在 `test_init_default_guided_mode_accepts_happy_path` 中增加：

```python
    assert "扫描仓库" in result.output
    assert "正在收集仓库文件、构建配置、CI、测试和文档证据" in result.output
    assert "正在请求 LLM 做结构化扫描" in result.output
    assert "正在调和 LLM 判断与 evidence" in result.output
    assert "扫描完成" in result.output
    assert result.output.index("扫描仓库") < result.output.index("扫描发现")
    assert result.output.index("扫描完成") < result.output.index("扫描发现")
```

- [ ] **Step 2: 新增扫描失败测试**

新增测试：

```python
def test_guided_init_scan_failure_prints_progress_and_no_formal_assets(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)

    def fail_scan(repo_path: Path):
        raise RuntimeError("synthetic scan failure")

    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="\n")
    output = _strip_ansi(result.output)

    assert result.exit_code != 0
    assert "扫描仓库" in output
    assert "扫描阶段失败" in output
    assert "未写入正式 Harness 资产" in output
    assert "请检查 LLM 配置、网络或扫描错误后重试" in output
    assert "synthetic scan failure" in output
    assert output.index("扫描仓库") < output.index("扫描阶段失败")
    assert not (repo / ".ai" / "project-inventory.json").exists()
    assert not (repo / ".ai" / "harness-config.yaml").exists()
    assert not (repo / ".ai" / "guides").exists()
    assert not (repo / ".ai" / "sensors").exists()
    assert not (repo / ".ai" / "skills").exists()
```

- [ ] **Step 3: 运行 RED**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path tests/integration/test_init_on_fixture_projects.py::test_guided_init_scan_failure_prints_progress_and_no_formal_assets -q
```

Expected: 新增断言失败，因为当前没有扫描进度文案。

### Task 2: 实现 guided 扫描进度输出

**Files:**
- Modify: `src/harness_builder_agent/tools/interactive_init.py`

- [ ] **Step 1: 修改 `run_guided_init()` 扫描段**

将当前扫描段改为：

```python
    _show_scan_progress_start(repo)
    trace.event("scan", "started", "Repository scan started.")
    try:
        inventory, commands = scan_repository(repo)
    except Exception:
        trace.event("scan", "failed", "Repository scan failed before writing formal Harness assets.")
        _show_scan_progress_failed()
        raise
    trace.event(
        "scan",
        "completed",
        "Repository scan completed.",
        {"primary_stack": inventory.primary_stack, "stacks": inventory.stacks, "command_count": len(commands.commands)},
    )
    _show_scan_progress_completed(inventory, commands)
```

- [ ] **Step 2: 新增渲染函数**

在 `_show_scan_findings()` 前新增：

```python
def _show_scan_progress_start(repo: Path) -> None:
    typer.echo("\n扫描仓库")
    typer.echo(f"- 目标仓库：{repo}")
    typer.echo("- 正在收集仓库文件、构建配置、CI、测试和文档证据。")
    typer.echo("- 正在识别构建、测试、验证命令、源码入口、模块线索和风险区域。")
    typer.echo("- 正在请求 LLM 做结构化扫描，并校验返回 schema。")
    typer.echo("- 正在调和 LLM 判断与 evidence；这个阶段可能需要一些时间。")


def _show_scan_progress_completed(inventory: ProjectInventory, commands: CommandCatalog) -> None:
    typer.echo("\n扫描完成")
    typer.echo("- 已完成 evidence 收集、LLM 结构化分析和扫描调和。")
    typer.echo(f"- 初步识别技术栈：{_stack_label(inventory.primary_stack)}。")
    typer.echo(f"- 初步识别验证命令数量：{len(commands.commands)}。")


def _show_scan_progress_failed() -> None:
    typer.echo("\n扫描阶段失败")
    typer.echo("- 未写入正式 Harness 资产。")
    typer.echo("- 请检查 LLM 配置、网络或扫描错误后重试。")
```

### Task 3: 更新文档与演进记录

**Files:**
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/evolution-log.md`

- [ ] **Step 1: 更新 init workflow**

在 Evidence / LLM 扫描前后补充 guided CLI 规则：首次 guided init 必须在阻塞扫描前展示阶段化进度，扫描失败要说明未写入正式 Harness 资产且继续显式失败。

- [ ] **Step 2: 更新 evolution log**

在文件顶部新增 `2026-05-31 Guided Init 扫描进度反馈`，记录 gap、用户故事、决策、sub agent 使用、验收和下一轮候选 gap。

### Task 4: 验证并提交

**Files:** all changed files.

- [ ] **Step 1: 运行 targeted tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path tests/integration/test_init_on_fixture_projects.py::test_guided_init_scan_failure_prints_progress_and_no_formal_assets -q
```

Expected: `2 passed`.

- [ ] **Step 2: 运行 guided init integration**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q
```

Expected: all tests passed.

- [ ] **Step 3: commit 前快速回归**

Run:

```bash
scripts/test-fast.sh
```

Expected: all tests passed.

- [ ] **Step 4: commit 与 push 前全量回归**

Run:

```bash
git add src/harness_builder_agent/tools/interactive_init.py tests/integration/test_init_on_fixture_projects.py docs/engineering/init-workflow.md docs/evolution-log.md docs/superpowers/specs/2026-05-31-guided-init-scan-progress-design.md docs/superpowers/plans/2026-05-31-guided-init-scan-progress.md
git commit -m "增加 guided init 扫描进度反馈"
scripts/test-full.sh
git push --no-verify origin main
```

Expected: fast 和 full 都通过后提交并推送。
