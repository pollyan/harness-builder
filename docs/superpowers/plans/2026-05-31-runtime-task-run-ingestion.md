# Runtime Task-Run 只读摄取 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 当 `.ai/task-runs` 由外部 Runtime 提供时，Harness Builder 可以只读校验、汇总并把它接入 Experience / Maturity / Benchmark。

**Architecture:** 新增 `runtime_task_run` schema 和 `runtime_task_runs` 工具模块，集中处理可选 Runtime 产物的 schema / consistency 校验。现有 `experience_index`、`maturity_evidence`、`benchmark`、`summarize_experience` 只消费该模块输出，不直接遍历 Runtime 文件细节。

**Tech Stack:** Python 3、Pydantic、PyYAML、pytest、Typer CLI 既有链路。

---

## File Structure

- Create: `src/harness_builder_agent/schemas/runtime_task_run.py`
  - 定义 `RuntimeSummary` 与 `RuntimeTaskRunSummary`。
- Create: `src/harness_builder_agent/tools/runtime_task_runs.py`
  - 负责列出、加载、校验和汇总 `.ai/task-runs/<task-id>/`。
- Modify: `src/harness_builder_agent/schemas/maturity_evidence.py`
  - 给 `ObservabilityEvidence` 增加 Runtime task-run 汇总字段。
- Modify: `src/harness_builder_agent/tools/experience_index.py`
  - 使用 Runtime summary 计算 task-run count 和 warning。
- Modify: `src/harness_builder_agent/tools/maturity_evidence.py`
  - 把 Runtime summary 写入 observability evidence。
- Modify: `src/harness_builder_agent/tools/benchmark.py`
  - 新增 optional runtime task-run content check。
- Modify: `src/harness_builder_agent/tools/summarize_experience.py`
  - 注入 Runtime summary 文本而不是目录名列表。
- Test: `tests/unit/test_runtime_task_runs.py`
- Modify Test: `tests/unit/test_experience_index.py`
- Modify Test: `tests/unit/test_maturity_evidence.py`
- Modify Test: `tests/unit/test_llm_experience_summarizer.py`
- Modify Test: `tests/integration/test_benchmark_command.py`
- Docs: `README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/evolution-log.md`

### Task 1: Runtime Task-Run Schema 和 Loader

- [ ] **Step 1: 写失败测试**

在 `tests/unit/test_runtime_task_runs.py` 新增：

```python
from pathlib import Path

import pytest
import yaml

from harness_builder_agent.tools.runtime_task_runs import (
    RuntimeTaskRunError,
    load_runtime_task_run,
    summarize_runtime_task_runs,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_task_run(ai: Path, task_id: str = "task-1", sensor_status: str = "failed") -> Path:
    run = ai / "task-runs" / task_id
    _write_yaml(
        run / "harness-map.yaml",
        {
            "schema_version": "1.0",
            "task_id": task_id,
            "task_type": "bugfix",
            "selected_workflow": "bugfix",
            "risk_level": "medium",
        },
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
                    "exit_code": 1 if sensor_status == "failed" else 0,
                    "duration_seconds": 3.2,
                    "summary": "pytest failed" if sensor_status == "failed" else "pytest passed",
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
            "status": "completed_with_sensor_failures" if sensor_status == "failed" else "completed",
            "sensor_status": sensor_status,
            "repair_attempts": 1,
            "unresolved_sensor_count": 1 if sensor_status == "failed" else 0,
            "risk_count": 1,
            "summary": "Runtime captured sensor outcome.",
        },
    )
    (run / "decision-log.md").write_text("# Decision Log\n\nInvestigated failing pytest.\n", encoding="utf-8")
    (run / "handoff-summary.md").write_text("# Handoff Summary\n\nPytest still fails.\n", encoding="utf-8")
    return run


def test_load_runtime_task_run_summarizes_sensor_outcomes(tmp_path: Path):
    ai = tmp_path / ".ai"
    run = _write_task_run(ai)

    summary = load_runtime_task_run(run)

    assert summary.task_id == "task-1"
    assert summary.source_path == ".ai/task-runs/task-1/"
    assert summary.failed_sensor_count == 1
    assert summary.skipped_sensor_count == 0
    assert summary.repair_attempts == 1


def test_summarize_runtime_task_runs_aggregates_valid_runs(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_task_run(ai, "task-1", "failed")
    _write_task_run(ai, "task-2", "passed")

    summary = summarize_runtime_task_runs(ai)

    assert summary.task_run_count == 2
    assert summary.failed_sensor_count == 1
    assert summary.passed_sensor_count == 1
    assert summary.source_paths == [".ai/task-runs/task-1/", ".ai/task-runs/task-2/"]


def test_runtime_task_run_rejects_inconsistent_sensor_status(tmp_path: Path):
    ai = tmp_path / ".ai"
    run = _write_task_run(ai, "task-1", "failed")
    payload = yaml.safe_load((run / "runtime-summary.yaml").read_text(encoding="utf-8"))
    payload["sensor_status"] = "passed"
    _write_yaml(run / "runtime-summary.yaml", payload)

    with pytest.raises(RuntimeTaskRunError, match="sensor_status_mismatch"):
        load_runtime_task_run(run)
```

- [ ] **Step 2: 运行测试并确认 RED**

Run: `.venv/bin/python -m pytest tests/unit/test_runtime_task_runs.py -q`

Expected: FAIL，原因是 `harness_builder_agent.tools.runtime_task_runs` 不存在。

- [ ] **Step 3: 最小实现 schema / loader**

创建 `src/harness_builder_agent/schemas/runtime_task_run.py` 和 `src/harness_builder_agent/tools/runtime_task_runs.py`，实现测试要求。

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `.venv/bin/python -m pytest tests/unit/test_runtime_task_runs.py -q`

Expected: `3 passed`。

### Task 2: Experience / Maturity 接入 Runtime Summary

- [ ] **Step 1: 写失败测试**

扩展 `tests/unit/test_experience_index.py` 和 `tests/unit/test_maturity_evidence.py`：

```python
def test_experience_index_records_valid_runtime_task_runs(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_valid_runtime_task_run(ai, task_id="task-1")

    index = build_experience_index(ai)

    assert index.runtime_task_run_count == 1
    assert any(source.path == ".ai/task-runs/" and source.item_count == 1 for source in index.sources)
    assert not any("runtime task-runs absent" in warning for warning in index.warnings)
```

```python
def test_maturity_evidence_includes_runtime_task_run_outcomes(tmp_path: Path):
    ai = _write_minimal_harness(tmp_path)
    _write_valid_runtime_task_run(ai, task_id="task-1", sensor_status="failed")

    evidence = collect_maturity_evidence(ai)

    assert evidence.observability.runtime_task_run_count == 1
    assert evidence.observability.runtime_failed_sensor_count == 1
    assert evidence.observability.runtime_unresolved_sensor_count == 1
```

- [ ] **Step 2: 运行 targeted tests 确认 RED**

Run: `.venv/bin/python -m pytest tests/unit/test_experience_index.py tests/unit/test_maturity_evidence.py -q`

Expected: FAIL，缺少新增字段或仍只计目录。

- [ ] **Step 3: 实现接入**

修改 `ExperienceIndex` 不新增字段，只改来源计数；修改 `ObservabilityEvidence` 增加：

```python
runtime_task_run_count: int = 0
runtime_failed_sensor_count: int = 0
runtime_skipped_sensor_count: int = 0
runtime_unresolved_sensor_count: int = 0
runtime_repair_attempt_count: int = 0
runtime_source_paths: list[str] = Field(default_factory=list)
```

`experience_index.py` 和 `maturity_evidence.py` 使用 `summarize_runtime_task_runs(ai)`。

- [ ] **Step 4: 运行 targeted tests 确认 GREEN**

Run: `.venv/bin/python -m pytest tests/unit/test_experience_index.py tests/unit/test_maturity_evidence.py -q`

Expected: PASS。

### Task 3: Benchmark Optional Runtime Check

- [ ] **Step 1: 写失败测试**

在 `tests/integration/test_benchmark_command.py` 增加：

```python
def test_benchmark_reports_absent_runtime_task_runs_as_optional(tmp_path: Path, monkeypatch):
    repo = _initialized_repo(tmp_path, monkeypatch)

    report = run_benchmark(repo)
    check = next(item for item in report["checks"] if item["id"] == "content:runtime-task-run-artifacts")

    assert check["passed"] is True
    assert check["present"] is False
```

```python
def test_benchmark_validates_present_runtime_task_runs(tmp_path: Path, monkeypatch):
    repo = _initialized_repo(tmp_path, monkeypatch)
    _write_valid_runtime_task_run(repo / ".ai", task_id="task-1", sensor_status="failed")

    report = run_benchmark(repo)
    check = next(item for item in report["checks"] if item["id"] == "content:runtime-task-run-artifacts")

    assert check["passed"] is True
    assert check["present"] is True
    assert check["task_run_count"] == 1
    assert check["failed_sensor_count"] == 1
```

```python
def test_benchmark_fails_invalid_runtime_task_run(tmp_path: Path, monkeypatch):
    repo = _initialized_repo(tmp_path, monkeypatch)
    run = _write_valid_runtime_task_run(repo / ".ai", task_id="task-1", sensor_status="failed")
    (run / "runtime-summary.yaml").unlink()

    report = run_benchmark(repo)
    check = next(item for item in report["checks"] if item["id"] == "content:runtime-task-run-artifacts")

    assert check["passed"] is False
    assert "missing_runtime_summary" in check["errors"]
    assert report["status"] == "failed"
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q`

Expected: FAIL，缺少 check id。

- [ ] **Step 3: 实现 benchmark check**

在 `_content_checks()` 中加入 `_runtime_task_run_artifacts_check(ai)`，调用 `summarize_runtime_task_runs(ai)`，缺失 task-runs 返回 optional passed。

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q`

Expected: PASS。

### Task 4: Experience Summary Source 注入真实 Runtime 内容

- [ ] **Step 1: 写失败测试**

在 `tests/unit/test_llm_experience_summarizer.py` 或新测试中覆盖 `_collect_sources()`：

```python
def test_collect_sources_includes_runtime_sensor_and_handoff_details(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_valid_runtime_task_run(ai, task_id="task-1", sensor_status="failed")

    sources = _collect_sources(tmp_path)

    runtime_source = sources[".ai/task-runs/task-1/"]
    assert "sensor failed" in runtime_source
    assert "pytest failed" in runtime_source
    assert "Pytest still fails." in runtime_source
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `.venv/bin/python -m pytest tests/unit/test_llm_experience_summarizer.py -q`

Expected: FAIL，目前只输出文件名列表。

- [ ] **Step 3: 实现 source text 渲染**

在 `runtime_task_runs.py` 增加 `render_runtime_task_run_source(run_dir)` 或在 summarizer 中复用 summary 对象渲染文本。

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `.venv/bin/python -m pytest tests/unit/test_llm_experience_summarizer.py -q`

Expected: PASS。

### Task 5: 文档与回归

- [ ] **Step 1: 更新文档**

更新：

- `README.md`：说明 Builder 不生成 task-runs，但会在存在时只读校验并纳入 Experience / Maturity / Benchmark。
- `docs/engineering/init-workflow.md`：更新 `experience-index.yaml` 和 maturity evidence 对 Runtime 的规则。
- `docs/engineering/sensor-and-gate-rules.md`：benchmark optional Runtime task-run 检查规则。
- `docs/evolution-log.md`：新增本轮中文演进记录。

- [ ] **Step 2: 运行 targeted 验证**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_runtime_task_runs.py tests/unit/test_experience_index.py tests/unit/test_maturity_evidence.py tests/unit/test_llm_experience_summarizer.py tests/integration/test_benchmark_command.py -q
```

Expected: PASS。

- [ ] **Step 3: 运行快速回归**

Run: `scripts/test-fast.sh`

Expected: PASS。

- [ ] **Step 4: 提交**

Run:

```bash
git add src tests README.md docs/engineering docs/evolution-log.md docs/superpowers/specs/2026-05-31-runtime-task-run-ingestion-design.md docs/superpowers/plans/2026-05-31-runtime-task-run-ingestion.md
git commit -m "接入 Runtime 任务过程数据只读校验"
```

Expected: 中文 commit 创建成功。

## Self-Review

- 本计划只做一个纵向 milestone：只读消费外部 Runtime 产物。
- 不恢复 `run` 命令，不执行 Sensors，不创建 `.ai/task-runs`。
- 测试先覆盖 schema / consistency / benchmark / maturity evidence，再实现。
- 过程文档和 commit message 使用中文。
