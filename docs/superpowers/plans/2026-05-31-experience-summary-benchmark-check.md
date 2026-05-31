# Experience Summary Benchmark Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make benchmark validate optional `.ai/experience/experience-summary.*` artifacts when present.

**Architecture:** Follow existing optional review artifact checks in `benchmark.py`. Add one check function, wire it into `_content_checks`, cover it with integration tests, and update gate docs.

**Tech Stack:** Python, pytest, Typer CLI integration tests, Pydantic schemas, YAML/Markdown artifact checks.

---

### Task 1: Add Failing Benchmark Tests

**Files:**
- Modify: `tests/integration/test_benchmark_command.py`

- [ ] **Step 1: Add helper for valid summary artifacts**

Add:

```python
def _write_valid_experience_summary(ai: Path) -> None:
    experience = ai / "experience"
    experience.mkdir(parents=True, exist_ok=True)
    (experience / "experience-summary.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "source": "llm_experience_summary",
                "review_status": "pending_harness_maintainer_review",
                "summary": "Sensor coverage is the main experience signal.",
                "findings": [
                    {
                        "id": "sensor-coverage-gap",
                        "kind": "sensor_feedback",
                        "title": "Sensor coverage gap",
                        "summary": "Pending improvements point to missing sensor coverage.",
                        "evidence_sources": [".ai/experience/pending-improvements.md"],
                        "confidence": "high",
                        "suggested_follow_up": "Draft a reviewed sensor candidate.",
                    }
                ],
                "warnings": ["Runtime task-runs are absent."],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (experience / "experience-summary.md").write_text(
        "# Experience Summary\n\n"
        "## Summary\n\nSensor coverage is the main experience signal.\n\n"
        "## Findings\n\n### Sensor coverage gap\n\n- evidence: `.ai/experience/pending-improvements.md`\n\n"
        "## Warnings\n\n- Runtime task-runs are absent.\n",
        encoding="utf-8",
    )
```

- [ ] **Step 2: Assert the happy-path check id is present**

In `test_benchmark_generates_report_for_java_fixture`, add:

```python
assert "content:experience-summary-artifact" in check_ids
```

- [ ] **Step 3: Add valid artifact test**

Add:

```python
def test_benchmark_accepts_valid_experience_summary_artifacts(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_experience_summary(ai)
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    summary = next(check for check in checks if check["id"] == "content:experience-summary-artifact")
    assert summary["passed"] is True
    assert summary["present"] is True
    assert summary["finding_count"] == 1
```

- [ ] **Step 4: Add outside evidence failure test**

Add:

```python
def test_benchmark_fails_experience_summary_with_outside_ai_evidence(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_experience_summary(ai)
    path = ai / "experience" / "experience-summary.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["findings"][0]["evidence_sources"] = ["README.md"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    summary = next(check for check in checks if check["id"] == "content:experience-summary-artifact")
    assert summary["passed"] is False
    assert "evidence_source_outside_ai" in summary["errors"]
```

- [ ] **Step 5: Add missing Markdown sections failure test**

Add:

```python
def test_benchmark_fails_experience_summary_when_markdown_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_experience_summary(ai)
    (ai / "experience" / "experience-summary.md").write_text("# Experience Summary\n", encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    summary = next(check for check in checks if check["id"] == "content:experience-summary-artifact")
    assert summary["passed"] is False
    assert "missing_markdown_sections" in summary["errors"]
```

- [ ] **Step 6: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py::test_benchmark_generates_report_for_java_fixture tests/integration/test_benchmark_command.py::test_benchmark_accepts_valid_experience_summary_artifacts tests/integration/test_benchmark_command.py::test_benchmark_fails_experience_summary_with_outside_ai_evidence tests/integration/test_benchmark_command.py::test_benchmark_fails_experience_summary_when_markdown_sections_are_missing -q
```

Expected: FAIL because `content:experience-summary-artifact` does not exist.

### Task 2: Implement Benchmark Check

**Files:**
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `docs/engineering/sensor-and-gate-rules.md`

- [ ] **Step 1: Import schema**

Add:

```python
from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
```

- [ ] **Step 2: Wire the check**

Add `_experience_summary_artifact_check(ai)` to `_content_checks` near the other optional review artifact checks.

- [ ] **Step 3: Add the check function**

Add:

```python
def _experience_summary_artifact_check(ai: Path) -> dict[str, Any]:
    yaml_path = ai / "experience" / "experience-summary.yaml"
    markdown_path = ai / "experience" / "experience-summary.md"
    if not yaml_path.exists() and not markdown_path.exists():
        return {"id": "content:experience-summary-artifact", "passed": True, "present": False}

    errors: list[str] = []
    if not yaml_path.exists() or not markdown_path.exists():
        errors.append("incomplete_experience_summary_artifact_pair")

    try:
        report = ExperienceSummaryReport.model_validate(yaml.safe_load(yaml_path.read_text(encoding="utf-8")))
    except Exception as exc:
        return {"id": "content:experience-summary-artifact", "passed": False, "present": True, "errors": [str(exc)]}

    if report.review_status != "pending_harness_maintainer_review":
        errors.append("summary_not_review_only")
    if any(not source.startswith(".ai/") for finding in report.findings for source in finding.evidence_sources):
        errors.append("evidence_source_outside_ai")

    markdown = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else ""
    required_sections = ["# Experience Summary", "## Summary", "## Findings", "## Warnings"]
    if any(section not in markdown for section in required_sections):
        errors.append("missing_markdown_sections")

    return {
        "id": "content:experience-summary-artifact",
        "passed": not errors,
        "present": True,
        "finding_count": len(report.findings),
        "errors": sorted(set(errors)),
    }
```

- [ ] **Step 4: Update gate docs**

Add a bullet to `docs/engineering/sensor-and-gate-rules.md` explaining optional Experience Summary artifact validation.

- [ ] **Step 5: Run GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py::test_benchmark_generates_report_for_java_fixture tests/integration/test_benchmark_command.py::test_benchmark_accepts_valid_experience_summary_artifacts tests/integration/test_benchmark_command.py::test_benchmark_fails_experience_summary_with_outside_ai_evidence tests/integration/test_benchmark_command.py::test_benchmark_fails_experience_summary_when_markdown_sections_are_missing -q
```

Expected: all targeted tests pass.

### Task 3: Verify And Commit

**Files:**
- Create: `docs/superpowers/specs/2026-05-31-experience-summary-benchmark-check-design.md`
- Create: `docs/superpowers/plans/2026-05-31-experience-summary-benchmark-check.md`
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/integration/test_benchmark_command.py`
- Modify: `docs/engineering/sensor-and-gate-rules.md`

- [ ] **Step 1: Run benchmark integration tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q
```

Expected: benchmark integration tests pass.

- [ ] **Step 2: Run fast regression before commit**

Run:

```bash
scripts/test-fast.sh
```

Expected: fast suite passes.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/engineering/sensor-and-gate-rules.md docs/superpowers/specs/2026-05-31-experience-summary-benchmark-check-design.md docs/superpowers/plans/2026-05-31-experience-summary-benchmark-check.md src/harness_builder_agent/tools/benchmark.py tests/integration/test_benchmark_command.py
git commit -m "feat: validate experience summary in benchmark"
```

- [ ] **Step 4: Run full regression and push**

Run:

```bash
scripts/test-full.sh
git push
scripts/check-ci.sh
```

Expected: local full suite passes before push, push succeeds, and CI status is checked after push.
