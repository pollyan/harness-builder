# Maturity Review Benchmark Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make benchmark validate optional maturity review artifacts when they exist.

**Architecture:** Add a deterministic content check next to the existing optional review checks. Reuse `MaturityReviewReport` and `ImprovementCandidateReport`, then validate cross-file candidate references, `.ai/` evidence boundaries, and required Markdown sections.

**Tech Stack:** Python, Pydantic, YAML, pytest integration tests.

---

### Task 1: Add Benchmark Tests

**Files:**
- Modify: `tests/integration/test_benchmark_command.py`

- [ ] **Step 1: Add valid maturity review helper**

```python
def _write_valid_maturity_review(ai: Path) -> None:
    review = ai / "review"
    review.mkdir(parents=True, exist_ok=True)
    improvements = yaml.safe_load((ai / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    source_id = improvements["candidates"][0]["id"]
    (review / "maturity-review.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "summary": "Candidates are aligned with maturity evidence.",
                "reviewer_model": "deepseek-test",
                "candidate_reviews": [
                    {
                        "candidate_id": source_id,
                        "decision": "support",
                        "rationale": "Candidate is grounded in maturity evidence.",
                        "risks": [],
                        "suggested_acceptance_checks": ["Run benchmark."],
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                    }
                ],
                "missing_candidates": [],
                "global_risks": [],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (review / "maturity-review.md").write_text(
        "# Maturity Review\n\n"
        "## Summary\n\nCandidates are aligned.\n\n"
        "## Candidate Reviews\n\n- candidate: support\n\n"
        "## Missing Candidates\n\n- None.\n\n"
        "## Global Risks\n\n- None.\n",
        encoding="utf-8",
    )
```

- [ ] **Step 2: Add check id assertion**

Add `"content:maturity-review-artifact"` to the generated benchmark report check ids.

- [ ] **Step 3: Add RED tests**

```python
def test_benchmark_records_absent_maturity_review_as_optional(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is True
    assert review["present"] is False


def test_benchmark_accepts_valid_maturity_review_artifacts(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_maturity_review(ai)
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is True
    assert review["present"] is True
    assert review["candidate_review_count"] == 1


def test_benchmark_fails_maturity_review_with_unknown_candidate(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_maturity_review(ai)
    path = ai / "review" / "maturity-review.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidate_reviews"][0]["candidate_id"] = "missing-candidate"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is False
    assert "unknown_candidate_id" in review["errors"]


def test_benchmark_fails_maturity_review_with_outside_ai_evidence(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_maturity_review(ai)
    path = ai / "review" / "maturity-review.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidate_reviews"][0]["evidence_sources"] = ["README.md"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is False
    assert "evidence_source_outside_ai" in review["errors"]


def test_benchmark_fails_maturity_review_when_markdown_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_maturity_review(ai)
    (ai / "review" / "maturity-review.md").write_text("# Maturity Review\n", encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is False
    assert "missing_markdown_sections" in review["errors"]
```

- [ ] **Step 4: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py::test_benchmark_records_absent_maturity_review_as_optional -q
```

Expected: FAIL because the content check does not exist.

### Task 2: Implement Benchmark Check

**Files:**
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `docs/engineering/sensor-and-gate-rules.md`

- [ ] **Step 1: Import `MaturityReviewReport`**

```python
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
```

- [ ] **Step 2: Include check in `_content_checks`**

Add `_maturity_review_artifact_check(ai)` after `_workflow_recommendation_review_check(ai)`.

- [ ] **Step 3: Add helper**

```python
def _maturity_review_artifact_check(ai: Path) -> dict[str, Any]:
    yaml_path = ai / "review" / "maturity-review.yaml"
    markdown_path = ai / "review" / "maturity-review.md"
    if not yaml_path.exists() and not markdown_path.exists():
        return {"id": "content:maturity-review-artifact", "passed": True, "present": False}

    errors: list[str] = []
    if not yaml_path.exists() or not markdown_path.exists():
        errors.append("incomplete_maturity_review_artifact_pair")

    try:
        report = MaturityReviewReport.model_validate(yaml.safe_load(yaml_path.read_text(encoding="utf-8")))
        improvements = ImprovementCandidateReport.model_validate(
            yaml.safe_load((ai / "improvement-candidates.yaml").read_text(encoding="utf-8"))
        )
    except Exception as exc:
        return {"id": "content:maturity-review-artifact", "passed": False, "present": True, "errors": [str(exc)]}

    known_candidate_ids = {candidate.id for candidate in improvements.candidates}
    for item in report.candidate_reviews:
        if item.candidate_id not in known_candidate_ids:
            errors.append("unknown_candidate_id")
        if any(not source.startswith(".ai/") for source in item.evidence_sources):
            errors.append("evidence_source_outside_ai")

    markdown = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else ""
    required_sections = ["# Maturity Review", "## Summary", "## Candidate Reviews", "## Missing Candidates", "## Global Risks"]
    if any(section not in markdown for section in required_sections):
        errors.append("missing_markdown_sections")

    return {
        "id": "content:maturity-review-artifact",
        "passed": not errors,
        "present": True,
        "candidate_review_count": len(report.candidate_reviews),
        "errors": sorted(set(errors)),
    }
```

- [ ] **Step 4: Update engineering doc**

Mention `.ai/review/maturity-review.yaml` and `.md` in the optional review artifact benchmark validation rule.

- [ ] **Step 5: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py::test_benchmark_records_absent_maturity_review_as_optional tests/integration/test_benchmark_command.py::test_benchmark_accepts_valid_maturity_review_artifacts tests/integration/test_benchmark_command.py::test_benchmark_fails_maturity_review_with_unknown_candidate tests/integration/test_benchmark_command.py::test_benchmark_fails_maturity_review_with_outside_ai_evidence tests/integration/test_benchmark_command.py::test_benchmark_fails_maturity_review_when_markdown_sections_are_missing -q
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
git add docs/engineering/sensor-and-gate-rules.md docs/superpowers/specs/2026-05-31-maturity-review-benchmark-check-design.md docs/superpowers/plans/2026-05-31-maturity-review-benchmark-check.md src/harness_builder_agent/tools/benchmark.py tests/integration/test_benchmark_command.py
git commit -m "feat: validate maturity reviews in benchmark"
```

- [ ] **Step 4: Run full regression and push**

Run:

```bash
scripts/test-full.sh
git push
scripts/check-ci.sh
```

Expected: local full suite passes before push; push succeeds; CI status is checked after push.
