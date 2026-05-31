# Workflow Recommendation Benchmark Checks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Validate optional workflow recommendation review artifacts during benchmark without making them required or restoring runtime execution.

**Architecture:** Extend `benchmark.py` with one focused optional content check that validates the `WorkflowRecommendationReport` schema, cross-references `harness-config.yaml`, and checks Markdown review sections. Add integration tests around `_content_checks` and update engineering docs to document the optional review-artifact gate.

**Tech Stack:** Python, Typer CLI integration tests, Pydantic schemas, YAML, pytest.

---

### Task 1: Add failing benchmark tests

**Files:**
- Modify: `tests/integration/test_benchmark_command.py`

- [x] **Step 1: Add valid recommendation fixture helper and assertions**

Add helper code in `tests/integration/test_benchmark_command.py`:

```python
def _write_valid_workflow_recommendation(ai: Path) -> None:
    review = ai / "review"
    review.mkdir(parents=True, exist_ok=True)
    (review / "workflow-routing-recommendation.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "task_id": "task-1",
                "task_brief": "Fix a regression in login validation.",
                "recommended_workflow": "bugfix",
                "matched_rule_ids": ["bugfix-intent"],
                "risk_level": "medium",
                "confidence": "high",
                "rationale": "The task is a defect repair and should use the bugfix workflow.",
                "required_guides": [".ai/guides/project-context.md"],
                "required_sensors": [".ai/sensors/verification.md"],
                "human_confirmation_required": False,
                "review_status": "pending_harness_maintainer_review",
                "evidence_sources": [".ai/harness-config.yaml", ".ai/maturity-evidence.yaml"],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (review / "workflow-routing-recommendation.md").write_text(
        "# Workflow Routing Recommendation\n\n"
        "## Task\n\nFix a regression in login validation.\n\n"
        "## Recommended Workflow\n\nbugfix\n\n"
        "## Matched Routing Rules\n\n- bugfix-intent\n\n"
        "## Required Harness Assets\n\n- .ai/guides/project-context.md\n\n"
        "## Review Boundary\n\npending_harness_maintainer_review\n",
        encoding="utf-8",
    )
```

- [x] **Step 2: Add absent optional artifact assertion**

Add:

```python
def test_benchmark_records_absent_workflow_recommendation_as_optional(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is True
    assert recommendation["present"] is False
```

- [x] **Step 3: Add valid optional artifact assertion**

Add:

```python
def test_benchmark_accepts_valid_workflow_recommendation_review_artifacts(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_workflow_recommendation(ai)
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is True
    assert recommendation["present"] is True
    assert recommendation["recommended_workflow"] == "bugfix"
```

- [x] **Step 4: Add invalid cross-reference assertions**

Add:

```python
def test_benchmark_fails_when_workflow_recommendation_references_unknown_workflow(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_workflow_recommendation(ai)
    path = ai / "review" / "workflow-routing-recommendation.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["recommended_workflow"] = "release"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is False
    assert "unknown_recommended_workflow" in recommendation["errors"]
```

Add:

```python
def test_benchmark_fails_when_workflow_recommendation_references_unknown_rule(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_workflow_recommendation(ai)
    path = ai / "review" / "workflow-routing-recommendation.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["matched_rule_ids"] = ["missing-rule"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is False
    assert "unknown_matched_rule_ids" in recommendation["errors"]
```

- [x] **Step 5: Add Markdown section assertion**

Add:

```python
def test_benchmark_fails_when_workflow_recommendation_markdown_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_workflow_recommendation(ai)
    (ai / "review" / "workflow-routing-recommendation.md").write_text("# Workflow Routing Recommendation\n", encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is False
    assert "missing_markdown_sections" in recommendation["errors"]
```

- [x] **Step 6: Run focused test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q
```

Expected: new tests fail because `content:workflow-recommendation-review` does not exist yet.

### Task 2: Implement benchmark check

**Files:**
- Modify: `src/harness_builder_agent/tools/benchmark.py`

- [x] **Step 1: Import schema**

Add:

```python
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
```

- [x] **Step 2: Include check in `_content_checks`**

Add `_workflow_recommendation_review_check(ai)` after `_maturity_routing_evidence_check(ai)`.

- [x] **Step 3: Implement helper**

Add a helper that:

```python
def _workflow_recommendation_review_check(ai: Path) -> dict[str, Any]:
    yaml_path = ai / "review" / "workflow-routing-recommendation.yaml"
    markdown_path = ai / "review" / "workflow-routing-recommendation.md"
    if not yaml_path.exists() and not markdown_path.exists():
        return {"id": "content:workflow-recommendation-review", "passed": True, "present": False}

    errors: list[str] = []
    if not yaml_path.exists() or not markdown_path.exists():
        errors.append("incomplete_recommendation_artifact_pair")

    try:
        config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))
        report = WorkflowRecommendationReport.model_validate(yaml.safe_load(yaml_path.read_text(encoding="utf-8")))
    except Exception as exc:
        return {"id": "content:workflow-recommendation-review", "passed": False, "present": True, "errors": [str(exc)]}

    available_workflows = set(config.workflows)
    available_rule_ids = {rule.id for rule in config.workflow_routing.rules}
    if report.recommended_workflow not in available_workflows:
        errors.append("unknown_recommended_workflow")
    if any(rule_id not in available_rule_ids for rule_id in report.matched_rule_ids):
        errors.append("unknown_matched_rule_ids")
    if report.review_status != "pending_harness_maintainer_review":
        errors.append("recommendation_not_review_only")
    if any(not source.startswith(".ai/") for source in report.evidence_sources):
        errors.append("evidence_source_outside_ai")

    markdown = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else ""
    required_sections = [
        "# Workflow Routing Recommendation",
        "## Task",
        "## Recommended Workflow",
        "## Matched Routing Rules",
        "## Required Harness Assets",
        "## Review Boundary",
    ]
    missing_sections = [section for section in required_sections if section not in markdown]
    if missing_sections:
        errors.append("missing_markdown_sections")

    return {
        "id": "content:workflow-recommendation-review",
        "passed": not errors,
        "present": True,
        "recommended_workflow": report.recommended_workflow,
        "matched_rule_count": len(report.matched_rule_ids),
        "errors": errors,
    }
```

- [x] **Step 4: Run focused test and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q
```

Expected: pass.

### Task 3: Update engineering documentation

**Files:**
- Modify: `docs/engineering/sensor-and-gate-rules.md`

- [x] **Step 1: Document optional review artifact benchmark checks**

Add under Benchmark rules:

```markdown
- Optional review artifacts generated by explicit LLM review commands must be validated when present. They are not required baseline files, but malformed schema, missing paired Markdown/YAML, invalid cross-file references, or loss of review-only status should fail benchmark.
```

- [x] **Step 2: Run doc grep**

Run:

```bash
rg -n "Optional review artifacts|workflow-recommendation-review" docs/engineering src tests
```

Expected: finds the new documentation plus benchmark/test references.

### Task 4: Verify and commit

**Files:**
- Modified tests, benchmark, docs, spec, plan.

- [x] **Step 1: Run focused benchmark tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q
```

Expected: pass.

- [x] **Step 2: Run fast regression before commit**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [x] **Step 3: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-05-31-workflow-recommendation-benchmark-checks-design.md docs/superpowers/plans/2026-05-31-workflow-recommendation-benchmark-checks.md tests/integration/test_benchmark_command.py src/harness_builder_agent/tools/benchmark.py docs/engineering/sensor-and-gate-rules.md
git commit -m "feat: validate workflow recommendation reviews in benchmark"
```

Expected: commit succeeds after pre-commit fast test.

### Self-Review

- Spec coverage: optional artifact, valid artifact, invalid workflow, invalid rule, missing Markdown sections, no runtime execution, and docs are covered.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: helper uses existing `WorkflowRecommendationReport`, `HarnessConfig`, and `_content_checks` patterns.
