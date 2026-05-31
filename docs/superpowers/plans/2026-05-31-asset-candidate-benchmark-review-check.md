# Asset Candidate Benchmark Review Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make benchmark validate optional review-only asset candidate artifacts when they exist.

**Architecture:** Add a content check beside the existing workflow recommendation review check. Reuse `AssetCandidateReport` and `ImprovementCandidateReport` schemas, then add deterministic cross-file and Markdown checks that schema validation cannot express.

**Tech Stack:** Python, Pydantic, YAML, pytest integration tests.

---

### Task 1: Add Benchmark Tests

**Files:**
- Modify: `tests/integration/test_benchmark_command.py`

- [ ] **Step 1: Import schema check target through existing content checks**

Add `"content:asset-candidate-review"` to the generated benchmark check id assertions.

- [ ] **Step 2: Add helper for valid asset candidates**

Add:

```python
def _write_valid_asset_candidates(ai: Path) -> None:
    review = ai / "review"
    review.mkdir(parents=True, exist_ok=True)
    improvements = yaml.safe_load((ai / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    source_id = improvements["candidates"][0]["id"]
    (review / "asset-candidates.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "source": "llm_maturity_review",
                "candidates": [
                    {
                        "id": "workflow-routing-policy-review",
                        "kind": "workflow_policy",
                        "source_candidate_id": source_id,
                        "source_review_decision": "support",
                        "suggested_path": ".ai/harness-config.yaml",
                        "title": "Review workflow routing policy",
                        "rationale": "Workflow recommendation evidence suggests a routing policy review.",
                        "draft_content": "workflow_routing:\\n  rules:\\n    - id: standard-escalation",
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                        "acceptance_checks": ["Benchmark content:workflow-routing-policy passes."],
                        "risk_level": "medium",
                        "review_status": "pending_harness_maintainer_review",
                    }
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    for filename, title in {
        "asset-candidate-guides.md": "Asset Candidate Guides",
        "asset-candidate-sensors.md": "Asset Candidate Sensors",
        "asset-candidate-workflows.md": "Asset Candidate Workflows",
    }.items():
        (review / filename).write_text(
            f"# {title}\\n\\n"
            "## Review workflow routing policy\\n\\n"
            "### Rationale\\n\\nReview rationale.\\n\\n"
            "### Draft Content\\n\\nDraft only.\\n\\n"
            "### Evidence Sources\\n\\n- .ai/maturity-evidence.yaml\\n\\n"
            "### Acceptance Checks\\n\\n- Benchmark content:workflow-routing-policy passes.\\n",
            encoding="utf-8",
        )
```

- [ ] **Step 3: Add RED tests**

Add tests:

```python
def test_benchmark_records_absent_asset_candidates_as_optional(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is True
    assert asset_candidates["present"] is False


def test_benchmark_accepts_valid_asset_candidate_review_artifacts(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is True
    assert asset_candidates["present"] is True
    assert asset_candidates["candidate_count"] == 1


def test_benchmark_fails_asset_candidate_with_unknown_source_candidate(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    path = ai / "review" / "asset-candidates.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidates"][0]["source_candidate_id"] = "missing-candidate"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is False
    assert "unknown_source_candidate_id" in asset_candidates["errors"]


def test_benchmark_fails_asset_candidate_with_outside_ai_evidence(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    path = ai / "review" / "asset-candidates.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidates"][0]["evidence_sources"] = ["README.md"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is False
    assert "evidence_source_outside_ai" in asset_candidates["errors"]


def test_benchmark_fails_asset_candidate_when_markdown_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    (ai / "review" / "asset-candidate-workflows.md").write_text("# Asset Candidate Workflows\\n", encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is False
    assert "missing_markdown_sections" in asset_candidates["errors"]
```

- [ ] **Step 4: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py::test_benchmark_records_absent_asset_candidates_as_optional -q
```

Expected: FAIL because the content check does not exist.

### Task 2: Implement Benchmark Check

**Files:**
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `docs/engineering/sensor-and-gate-rules.md`

- [ ] **Step 1: Import `AssetCandidateReport`**

Add:

```python
from harness_builder_agent.schemas.asset_candidate import AssetCandidateReport
```

- [ ] **Step 2: Include check in `_content_checks`**

Add `_asset_candidate_review_check(ai)` after `_workflow_recommendation_review_check(ai)`.

- [ ] **Step 3: Add helper function**

Implement:

```python
def _asset_candidate_review_check(ai: Path) -> dict[str, Any]:
    yaml_path = ai / "review" / "asset-candidates.yaml"
    markdown_paths = [
        ai / "review" / "asset-candidate-guides.md",
        ai / "review" / "asset-candidate-sensors.md",
        ai / "review" / "asset-candidate-workflows.md",
    ]
    present_paths = [path for path in [yaml_path, *markdown_paths] if path.exists()]
    if not present_paths:
        return {"id": "content:asset-candidate-review", "passed": True, "present": False}

    errors: list[str] = []
    if not yaml_path.exists() or len(present_paths) != 4:
        errors.append("incomplete_asset_candidate_artifact_set")

    try:
        report = AssetCandidateReport.model_validate(yaml.safe_load(yaml_path.read_text(encoding="utf-8")))
        improvements = ImprovementCandidateReport.model_validate(
            yaml.safe_load((ai / "improvement-candidates.yaml").read_text(encoding="utf-8"))
        )
    except Exception as exc:
        return {"id": "content:asset-candidate-review", "passed": False, "present": True, "errors": [str(exc)]}

    known_candidate_ids = {candidate.id for candidate in improvements.candidates}
    for candidate in report.candidates:
        if (
            candidate.source_candidate_id
            and candidate.source_review_decision != "missing"
            and candidate.source_candidate_id not in known_candidate_ids
        ):
            errors.append("unknown_source_candidate_id")
        if not candidate.suggested_path.startswith(".ai/"):
            errors.append("suggested_path_outside_ai")
        if any(not source.startswith(".ai/") for source in candidate.evidence_sources):
            errors.append("evidence_source_outside_ai")

    required_sections = ["### Rationale", "### Draft Content", "### Evidence Sources", "### Acceptance Checks"]
    for path in markdown_paths:
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if any(section not in text for section in required_sections):
            errors.append("missing_markdown_sections")
            break

    return {
        "id": "content:asset-candidate-review",
        "passed": not errors,
        "present": True,
        "candidate_count": len(report.candidates),
        "errors": sorted(set(errors)),
    }
```

- [ ] **Step 4: Update engineering doc**

Clarify that optional asset candidate review artifacts are part of the optional LLM review artifact benchmark validation set.

- [ ] **Step 5: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py::test_benchmark_records_absent_asset_candidates_as_optional tests/integration/test_benchmark_command.py::test_benchmark_accepts_valid_asset_candidate_review_artifacts tests/integration/test_benchmark_command.py::test_benchmark_fails_asset_candidate_with_unknown_source_candidate tests/integration/test_benchmark_command.py::test_benchmark_fails_asset_candidate_with_outside_ai_evidence tests/integration/test_benchmark_command.py::test_benchmark_fails_asset_candidate_when_markdown_sections_are_missing -q
```

Expected: all focused tests pass.

### Task 3: Verify And Commit

**Files:**
- Created spec and plan files.
- Modified benchmark implementation, integration tests, and engineering docs.

- [ ] **Step 1: Run benchmark integration file**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q
```

Expected: benchmark integration tests pass.

- [ ] **Step 2: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: fast suite passes.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/engineering/sensor-and-gate-rules.md docs/superpowers/specs/2026-05-31-asset-candidate-benchmark-review-check-design.md docs/superpowers/plans/2026-05-31-asset-candidate-benchmark-review-check.md src/harness_builder_agent/tools/benchmark.py tests/integration/test_benchmark_command.py
git commit -m "feat: validate asset candidate reviews in benchmark"
```

- [ ] **Step 4: Run full regression and push**

Run:

```bash
scripts/test-full.sh
git push
scripts/check-ci.sh
```

Expected: local full suite passes before push; push succeeds; CI status is checked after push.
