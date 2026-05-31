# Guided Init 扫描内部阶段进度 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让首次 guided `init` 在真实扫描内部阶段显示进度，避免 `scan_repository()` 长时间阻塞时用户看不到当前阶段。

**Architecture:** `scan_repository()` 增加 optional progress callback 和 `ScanProgressEvent`，默认不改变行为。guided `init` 通过兼容 wrapper 仅在真实函数支持 progress 时传入 renderer；非交互路径不传 progress。

**Tech Stack:** Python dataclass、typing Callable / Literal、Typer、pytest。

---

### Task 1: 写 RED 测试

**Files:**
- Modify: `tests/unit/test_scan_repo.py`
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [x] **Step 1: 新增 unit event sequence 测试**

在 `tests/unit/test_scan_repo.py` 添加：

```python
def test_scan_repository_reports_progress_for_each_stage(tmp_path: Path):
    (tmp_path / "pom.xml").write_text("<project><artifactId>demo</artifactId></project>", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "Demo.java").write_text("class Demo {}", encoding="utf-8")
    events = []

    def planner_caller(_messages):
        return json.dumps(
            {
                "schema_version": "1.0",
                "requested_paths": ["src/Demo.java"],
                "risk_focus": [],
                "rationale": "Read source entry.",
                "confidence": "high",
            }
        )

    def scan_caller(_messages):
        return _llm_response("java-spring")

    scan_repository(
        tmp_path,
        llm_caller=scan_caller,
        evidence_planner_caller=planner_caller,
        progress=events.append,
    )

    assert [(event.phase, event.status) for event in events] == [
        ("collect-evidence", "started"),
        ("collect-evidence", "completed"),
        ("plan-evidence-expansion", "started"),
        ("plan-evidence-expansion", "completed"),
        ("expand-evidence", "started"),
        ("expand-evidence", "completed"),
        ("llm-scan", "started"),
        ("llm-scan", "completed"),
        ("reconcile-scan", "started"),
        ("reconcile-scan", "completed"),
    ]
    assert events[1].details["evidence_file_count"] >= 1
    assert events[5].details["requested_path_count"] == 1
    assert events[-1].details["command_count"] == 1
```

- [x] **Step 2: 扩展 guided happy path transcript 断言**

在 `test_init_default_guided_mode_accepts_happy_path` 中增加：

```python
    assert "当前阶段：收集仓库 evidence" in result.output
    assert "当前阶段：请求 LLM 规划补充 evidence" in result.output
    assert "当前阶段：读取 LLM 请求的补充 evidence" in result.output
    assert "当前阶段：请求 LLM 做最终结构化扫描" in result.output
    assert "当前阶段：调和扫描结果" in result.output
    assert result.output.index("当前阶段：收集仓库 evidence") < result.output.index("扫描完成")
```

- [x] **Step 3: 新增非交互输出边界测试**

新增或扩展非交互测试，断言：

```python
    assert "当前阶段：收集仓库 evidence" not in result.output
```

- [x] **Step 4: 运行 RED**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_scan_repo.py::test_scan_repository_reports_progress_for_each_stage tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path -q
```

Expected: 失败，因为当前 `scan_repository()` 不支持 `progress`。

### Task 2: 实现 scan progress callback

**Files:**
- Modify: `src/harness_builder_agent/tools/scan_repo.py`

- [x] **Step 1: 新增事件 dataclass 和类型**

```python
from dataclasses import dataclass, field
from typing import Literal

@dataclass(frozen=True)
class ScanProgressEvent:
    phase: str
    status: Literal["started", "completed"]
    message: str
    details: dict[str, object] = field(default_factory=dict)

ScanProgressCallback = Callable[[ScanProgressEvent], None]
```

- [x] **Step 2: 包装每个阶段**

在 `scan_repository()` 各阶段前后调用 `_emit_progress(progress, ...)`，保持原返回值和异常行为不变。

### Task 3: guided init 接入 progress renderer

**Files:**
- Modify: `src/harness_builder_agent/tools/interactive_init.py`

- [x] **Step 1: 新增 `_scan_repository_for_guided_init()`**

使用 `inspect.signature(scan_repository)` 判断是否支持 `progress` 参数；支持时传 `_guided_scan_progress`，否则按旧签名调用。

- [x] **Step 2: 新增 `_guided_scan_progress()`**

按 phase/status 输出中文行：

```python
def _guided_scan_progress(event: ScanProgressEvent) -> None:
    label = {...}.get(event.phase, event.message)
    if event.status == "started":
        typer.echo(f"- 当前阶段：{label}")
    else:
        typer.echo(f"  已完成：{label}")
```

- [x] **Step 3: guided scan 调用改为 wrapper**

把 `inventory, commands = scan_repository(repo)` 改为 `inventory, commands = _scan_repository_for_guided_init(repo)`。

### Task 4: 文档和演进记录

**Files:**
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/evolution-log.md`

- [x] **Step 1: 更新 init workflow**

补充 guided `init` 必须通过 scan progress callback 展示内部阶段，且非交互不承担该输出契约。

- [x] **Step 2: 更新 evolution log**

新增 `2026-05-31 Guided Init 扫描内部阶段进度`。

### Task 5: 验证并提交

**Files:** all changed files.

- [x] **Step 1: targeted tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_scan_repo.py::test_scan_repository_reports_progress_for_each_stage tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path -q
```

Expected: `2 passed`.

- [x] **Step 2: guided integration and scan unit**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_scan_repo.py tests/integration/test_init_on_fixture_projects.py -q
```

Expected: all passed.

- [ ] **Step 3: fast / full / push**

Run:

```bash
scripts/test-fast.sh
git add src/harness_builder_agent/tools/scan_repo.py src/harness_builder_agent/tools/interactive_init.py tests/unit/test_scan_repo.py tests/integration/test_init_on_fixture_projects.py docs/engineering/init-workflow.md docs/evolution-log.md docs/superpowers/specs/2026-05-31-guided-init-scan-stage-progress-design.md docs/superpowers/plans/2026-05-31-guided-init-scan-stage-progress.md
git commit -m "增加guided-init扫描内部阶段进度"
scripts/test-full.sh
git push --no-verify origin main
```
