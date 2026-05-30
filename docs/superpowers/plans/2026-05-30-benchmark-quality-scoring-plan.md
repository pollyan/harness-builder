# Benchmark Quality Scoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic quality scoring to `benchmark-report.yaml` while preserving existing hard benchmark pass/fail semantics.

**Architecture:** Extend the benchmark report schema with quality status, categorized score items, and summary fields. Implement deterministic scoring helpers in `benchmark.py`, feed them into `run_benchmark`, and add tests for passed, degraded, and failed quality outcomes.

**Tech Stack:** Python 3.11+, Pydantic, PyYAML, pytest.

---

## File Structure

Modify:

- `src/harness_builder_agent/schemas/benchmark_report.py`: add quality score schema fields.
- `src/harness_builder_agent/tools/benchmark.py`: compute `quality_scores`, `quality_summary`, and `quality_status`.
- `tests/unit/test_schema_contracts.py`: schema coverage for quality report fields.
- `tests/integration/test_benchmark_command.py`: passed/degraded/failed benchmark report scenarios.
- `README.md`: explain `status` vs `quality_status`.
- `docs/engineering/sensor-and-gate-rules.md`: add quality scoring rules.
- `docs/todos/benchmark-quality-scoring.md`: mark implemented.

Do not change:

- CLI exit behavior: `benchmark` exits non-zero only when `status != passed`.
- Acceptance test scope.
- DeepSeek or scan behavior.

---

### Task 1: Benchmark Report Quality Schema

**Files:**
- Modify: `src/harness_builder_agent/schemas/benchmark_report.py`
- Modify: `tests/unit/test_schema_contracts.py`

- [ ] **Step 1: Write failing schema test**

Append to `tests/unit/test_schema_contracts.py`:

```python
from harness_builder_agent.schemas.benchmark_report import BenchmarkReport


def test_benchmark_report_accepts_quality_scores():
    report = BenchmarkReport(
        repo_name="demo",
        profile="java-spring",
        status="passed",
        quality_status="degraded",
        checks=[{"id": "content:guides-quality", "passed": True}],
        quality_scores={
            "guide_quality": {
                "evidence_reference": {
                    "score": 3,
                    "max_score": 5,
                    "passed": False,
                    "reasons": ["来源证据章节存在但缺少路径。"],
                    "recommendations": ["在 guide 中补充 evidence path。"],
                }
            }
        },
        quality_summary={
            "total_score": 60,
            "minimum_score": 3,
            "degraded_items": ["guide_quality.evidence_reference"],
            "failed_items": [],
        },
    )

    payload = report.model_dump(mode="json")

    assert payload["quality_status"] == "degraded"
    assert payload["quality_scores"]["guide_quality"]["evidence_reference"]["score"] == 3
    assert payload["quality_summary"]["degraded_items"] == ["guide_quality.evidence_reference"]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_benchmark_report_accepts_quality_scores -q
```

Expected: FAIL because `BenchmarkReport` does not accept `quality_status`, `quality_scores`, or `quality_summary`.

- [ ] **Step 3: Implement schema**

Modify `src/harness_builder_agent/schemas/benchmark_report.py`:

```python
class QualityScoreItem(BaseModel):
    score: int
    max_score: int = 5
    passed: bool
    reasons: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class QualitySummary(BaseModel):
    total_score: int
    minimum_score: int
    degraded_items: list[str] = Field(default_factory=list)
    failed_items: list[str] = Field(default_factory=list)
```

Extend `BenchmarkReport`:

```python
    quality_status: Literal["passed", "degraded", "failed"] = "failed"
    quality_scores: dict[str, dict[str, QualityScoreItem]] = Field(default_factory=dict)
    quality_summary: QualitySummary | None = None
```

- [ ] **Step 4: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_benchmark_report_accepts_quality_scores -q
scripts/test-fast.sh
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/harness_builder_agent/schemas/benchmark_report.py tests/unit/test_schema_contracts.py
git commit -m "feat: add benchmark quality schema"
```

---

### Task 2: Deterministic Quality Scoring Helpers

**Files:**
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/integration/test_benchmark_command.py`

- [ ] **Step 1: Write failing helper tests through benchmark reports**

In `tests/integration/test_benchmark_command.py`, add assertions to the existing successful benchmark test:

```python
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text(encoding="utf-8"))
    assert report["quality_status"] in {"passed", "degraded"}
    assert "scan_quality" in report["quality_scores"]
    assert "guide_quality" in report["quality_scores"]
    assert "sensor_quality" in report["quality_scores"]
    assert "workflow_quality" in report["quality_scores"]
    assert report["quality_summary"]["total_score"] >= 0
```

Add test:

```python
def test_benchmark_degrades_quality_when_guide_lacks_evidence_reference(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    report = run_benchmark(repo, "java-spring")

    guide = repo / ".ai" / "guides" / "project-context.md"
    guide.write_text(guide.read_text(encoding="utf-8").replace("## 来源证据", "## 来源说明"), encoding="utf-8")
    report = run_benchmark(repo, "java-spring")

    assert report["status"] == "passed"
    assert report["quality_status"] == "degraded"
    item = report["quality_scores"]["guide_quality"]["evidence_reference"]
    assert item["score"] < 5
    assert item["passed"] is False
```

If `run_benchmark()` rewrites assets before checking and hides the corruption, split helper scoring into a callable `_quality_scores(ai, inventory, checks)` and test it directly with a prepared `.ai` directory.

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q
```

Expected: FAIL because report has no quality fields.

- [ ] **Step 3: Implement quality scoring helpers**

In `src/harness_builder_agent/tools/benchmark.py`, add:

```python
def _score_item(score: int, reasons: list[str] | None = None, recommendations: list[str] | None = None) -> dict[str, Any]:
    return {
        "score": score,
        "max_score": 5,
        "passed": score >= 4,
        "reasons": reasons or [],
        "recommendations": recommendations or [],
    }
```

Add `_quality_scores(ai, inventory)` returning:

```python
{
    "scan_quality": {
        "evidence_coverage": _score_evidence_coverage(ai),
        "stack_confidence": _score_stack_confidence(ai),
        "command_reliability": _score_command_reliability(ai),
    },
    "guide_quality": {
        "specificity": _score_guide_specificity(ai, inventory),
        "evidence_reference": _score_guide_evidence_reference(ai),
        "stack_specificity": _score_guide_stack_specificity(ai, inventory),
    },
    "sensor_quality": {
        "executable_gate": _score_executable_gate(ai),
        "failure_policy": _score_failure_policy(ai),
        "missing_capability_clarity": _score_missing_capability_clarity(ai),
    },
    "workflow_quality": {
        "skill_reference_integrity": _score_skill_reference_integrity(ai),
        "runtime_trace_completeness": _score_runtime_trace_completeness(ai),
    },
}
```

Implement each helper using deterministic file reads already used in benchmark checks. If a file cannot be read, return score `0` with a reason.

Add summary:

```python
def _quality_summary(scores: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    flat = [(f"{category}.{name}", item) for category, items in scores.items() for name, item in items.items()]
    total_possible = len(flat) * 5
    total = sum(item["score"] for _name, item in flat)
    total_score = int(round((total / total_possible) * 100)) if total_possible else 0
    minimum_score = min((item["score"] for _name, item in flat), default=0)
    degraded_items = [name for name, item in flat if 0 < item["score"] < 4]
    failed_items = [name for name, item in flat if item["score"] == 0]
    return {
        "total_score": total_score,
        "minimum_score": minimum_score,
        "degraded_items": degraded_items,
        "failed_items": failed_items,
    }
```

Add status:

```python
def _quality_status(hard_status: str, summary: dict[str, Any]) -> str:
    if hard_status == "failed" or summary["failed_items"]:
        return "failed"
    if summary["degraded_items"]:
        return "degraded"
    return "passed"
```

- [ ] **Step 4: Attach quality fields to report**

In `run_benchmark`, before building report:

```python
    quality_scores = _quality_scores(ai, inventory)
    quality_summary = _quality_summary(quality_scores)
```

Build report with:

```python
        "quality_scores": quality_scores,
        "quality_summary": quality_summary,
        "quality_status": _quality_status(status, quality_summary),
```

Use a local `status` variable to avoid computing hard status twice.

- [ ] **Step 5: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q
scripts/test-fast.sh
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/harness_builder_agent/tools/benchmark.py tests/integration/test_benchmark_command.py
git commit -m "feat: score benchmark quality"
```

---

### Task 3: Failed and Degraded Report Coverage

**Files:**
- Modify: `tests/integration/test_benchmark_command.py`
- Modify: `src/harness_builder_agent/tools/benchmark.py`

- [ ] **Step 1: Strengthen failed report test**

In the existing hard gate skipped/failed benchmark test, assert:

```python
    assert report["status"] == "failed"
    assert report["quality_status"] == "failed"
    assert report["quality_summary"]["failed_items"] or report["quality_summary"]["degraded_items"]
```

- [ ] **Step 2: Add command reliability degraded test**

Add:

```python
def test_benchmark_degrades_command_reliability_for_low_confidence_hard_gate(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    report = run_benchmark(repo, "java-spring")

    catalog_path = repo / ".ai" / "command-catalog.yaml"
    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    catalog["commands"][0]["confidence"] = "low"
    catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True), encoding="utf-8")
    scores = _quality_scores(repo / ".ai", ProjectInventory.model_validate_json((repo / ".ai" / "project-inventory.json").read_text()))

    assert scores["scan_quality"]["command_reliability"]["score"] < 4
    assert scores["scan_quality"]["command_reliability"]["passed"] is False
```

Import `_quality_scores` and `ProjectInventory` in the test file.

- [ ] **Step 3: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q
scripts/test-fast.sh
```

Expected: PASS.

- [ ] **Step 4: Commit**

Run:

```bash
git add src/harness_builder_agent/tools/benchmark.py tests/integration/test_benchmark_command.py
git commit -m "test: cover degraded benchmark quality"
```

---

### Task 4: Docs, Todo Status, and Final Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/engineering/sensor-and-gate-rules.md`
- Modify: `docs/todos/benchmark-quality-scoring.md`

- [ ] **Step 1: Update docs**

In `README.md`, add under benchmark:

```markdown
`benchmark-report.yaml` 中：

- `status` 表示硬验收是否通过。
- `quality_status` 表示质量评分结论：`passed`、`degraded` 或 `failed`。
- `quality_scores` 给出 scan、guide、sensor、workflow 的分项评分、原因和建议。
```

In `docs/engineering/sensor-and-gate-rules.md`, add Benchmark quality scoring rules:

```markdown
Benchmark 质量评分应覆盖 scan_quality、guide_quality、sensor_quality、workflow_quality。质量评分不能替代 hard gate；hard gate failed/skipped 仍必须让 benchmark hard status failed。
```

In `docs/todos/benchmark-quality-scoring.md`:

```markdown
- 状态：implemented

## 实现结果

- `benchmark-report.yaml` 已包含 `quality_status`、`quality_scores` 和 `quality_summary`。
- 评分覆盖 scan、guide、sensor、workflow 四类。
- hard `status` 保持现有 pass/fail 语义，`quality_status` 表达 passed/degraded/failed。
- 已补充 passed、degraded、failed 报告测试。
```

- [ ] **Step 2: Run verification**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py tests/integration/test_benchmark_command.py -q
scripts/test-fast.sh
```

Expected: PASS.

- [ ] **Step 3: Commit**

Run:

```bash
git add README.md docs/engineering/sensor-and-gate-rules.md docs/todos/benchmark-quality-scoring.md
git commit -m "docs: mark benchmark quality scoring implemented"
```

---

## Final Verification for This Todo

Run:

```bash
scripts/test-fast.sh
```

Before push or final goal completion, run:

```bash
scripts/test-full.sh
```

Expected:

- Fast tests pass.
- Acceptance tests pass with real DeepSeek and real benchmark repositories.
- `docs/todos/benchmark-quality-scoring.md` is implemented.
- `benchmark-report.yaml` contains `quality_status`, `quality_scores`, and `quality_summary`.

