# Guided Init 扫描失败退出边界硬化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让首次 guided `init` 的扫描失败以 CLI 友好方式显式退出，并留下唯一、可审计的 scan failure trace。

**Architecture:** 在 guided init 扫描失败分支 finish trace 后抛出 `typer.Exit(1)`；CLI 外层透传 Typer 控制流异常。测试在现有 guided init integration 中补强 output、trace.yaml、events.jsonl 和正式资产未写入断言。

**Tech Stack:** Python、Typer、pytest、Typer `CliRunner`、现有 `GenerationTrace`。

---

### Task 1: 补强失败路径测试

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [x] **Step 1: 在现有扫描失败测试中增加 trace 断言**

断言内容：

```python
    run_dirs = sorted((repo / ".ai" / "runs").iterdir())
    assert len(run_dirs) == 1
    trace = yaml.safe_load((run_dirs[0] / "trace.yaml").read_text(encoding="utf-8"))
    assert trace["status"] == "failed"
    assert trace["summary"]["error_type"] == "RuntimeError"
    assert trace["summary"]["scan_error"] == "synthetic scan failure"
    events = [
        json.loads(line)
        for line in (run_dirs[0] / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert any(
        event["stage"] == "scan"
        and event["event_type"] == "failed"
        and event["details"]["error_type"] == "RuntimeError"
        and event["details"]["error"] == "synthetic scan failure"
        for event in events
    )
    assert not any(event["stage"] == "init" and event["event_type"] == "failed" for event in events)
```

- [x] **Step 2: 运行目标测试**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_scan_failure_prints_progress_and_no_formal_assets -q
```

Observed: 当前工作区已有实现满足该契约，测试通过。

### Task 2: 收口实现

**Files:**
- Modify: `src/harness_builder_agent/tools/interactive_init.py`
- Modify: `src/harness_builder_agent/cli.py`

- [x] **Step 1: guided scan failure 写 trace 并以 Typer exit 退出**

目标代码语义：

```python
    except Exception as exc:
        trace.event(
            "scan",
            "failed",
            "Repository scan failed before writing formal Harness assets.",
            {"error_type": type(exc).__name__, "error": str(exc)},
        )
        _show_scan_progress_failed(exc)
        trace.finish("failed", {"error_type": type(exc).__name__, "scan_error": str(exc)})
        raise typer.Exit(code=1) from exc
```

- [x] **Step 2: CLI 外层透传 Typer 控制流异常**

目标代码语义：

```python
    except (typer.Exit, typer.Abort):
        raise
    except Exception as exc:
        ...
```

### Task 3: 同步文档

**Files:**
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/evolution-log.md`
- Create: `docs/superpowers/specs/2026-06-01-guided-init-scan-failure-exit-design.md`
- Create: `docs/superpowers/plans/2026-06-01-guided-init-scan-failure-exit.md`

- [x] **Step 1: 更新 init workflow**

补充规则：guided 扫描失败必须输出原因、影响和下一步；trace summary 必须记录 scan error；CLI 应以失败退出但不展示原始 traceback；外层不应重复写 `init failed`。

- [x] **Step 2: 更新 evolution log**

记录本轮 Gap Analysis 摘要、工程信任故事、决策、sub agent 使用、验收方式、完成内容、验证结果和 Self-Harness Gate。

### Task 4: 验证与提交

**Files:** all changed files.

- [x] **Step 1: 运行 targeted regression**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_scan_failure_prints_progress_and_no_formal_assets -q
```

Expected: `1 passed`.

- [x] **Step 2: 运行 diff 检查和 commit 前快速回归**

Run:

```bash
git diff --check
scripts/test-fast.sh
```

Expected: no whitespace errors, fast regression passes.

- [x] **Step 3: 创建中文 commit**

Run:

```bash
git add src/harness_builder_agent/cli.py src/harness_builder_agent/tools/interactive_init.py tests/integration/test_init_on_fixture_projects.py docs/engineering/init-workflow.md docs/evolution-log.md docs/superpowers/specs/2026-06-01-guided-init-scan-failure-exit-design.md docs/superpowers/plans/2026-06-01-guided-init-scan-failure-exit.md
git commit -m "硬化 guided init 扫描失败边界"
```
