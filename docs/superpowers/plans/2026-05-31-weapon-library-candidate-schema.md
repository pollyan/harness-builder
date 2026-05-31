# Weapon Library Candidate Schema Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Pydantic schema for `.ai/experience/weapon-library-candidates.yaml` and use it during generation and benchmark validation.

**Architecture:** Introduce a focused schema module for init-time LLM enhancement candidates. Keep guided decision mutation dict-based at the writer boundary, but validate the generated and persisted machine contract through `WeaponLibraryCandidateReport`.

**Tech Stack:** Python, Pydantic, pytest, YAML benchmark artifacts.

---

### Task 1: Add Failing Schema And Generation Tests

**Files:**
- Modify: `tests/unit/test_schema_contracts.py`
- Modify: `tests/unit/test_llm_enhancement_candidates.py`
- Modify: `tests/unit/test_write_assets.py`
- Modify: `tests/integration/test_benchmark_command.py`

- [ ] **Step 1: Add schema import and invalid-status test**

In `tests/unit/test_schema_contracts.py`, import:

```python
from pydantic import ValidationError
from harness_builder_agent.schemas.weapon_library_candidate import WeaponLibraryCandidateReport
```

Add:

```python
def test_weapon_library_candidate_report_rejects_invalid_status():
    with pytest.raises(ValidationError):
        WeaponLibraryCandidateReport.model_validate(
            {
                "schema_version": "1.0",
                "source": "llm_scan_proposal",
                "candidates": [
                    {
                        "id": "llm-guide-001",
                        "candidate_type": "guide",
                        "status": "applied",
                        "title": "Guide",
                        "rationale": "Needs review.",
                        "evidence": [".ai/project-inventory.json"],
                        "source": "llm_scan_proposal",
                        "human_confirmation_required": True,
                    }
                ],
            }
        )
```

- [ ] **Step 2: Add generation type test**

In `tests/unit/test_write_assets.py`, add:

```python
from harness_builder_agent.schemas.weapon_library_candidate import WeaponLibraryCandidateReport
from harness_builder_agent.tools.llm_enhancement_candidates import build_llm_enhancement_candidates
```

Add a test using existing project inventory / command helpers in the file:

```python
def test_llm_enhancement_candidates_returns_schema_report(tmp_path: Path):
    report = build_llm_enhancement_candidates(_inventory(tmp_path), _commands())

    assert isinstance(report, WeaponLibraryCandidateReport)
    assert report.schema_version == "1.0"
    assert report.candidates
    assert all(candidate.status == "candidate" for candidate in report.candidates)
```

- [ ] **Step 3: Add benchmark invalid persisted status test**

In `tests/integration/test_benchmark_command.py`, add:

```python
def test_benchmark_fails_weapon_library_candidates_with_invalid_status(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    path = ai / "experience" / "weapon-library-candidates.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidates"][0]["status"] = "applied"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    checks = _llm_enhancement_checks(ai)

    schema = next(check for check in checks if check["id"] == "schema:weapon-library-candidates")
    assert schema["passed"] is False
```

Also import `_llm_enhancement_checks` from `harness_builder_agent.tools.benchmark`.

- [ ] **Step 4: Update existing enhancement candidate test expectations**

In `tests/unit/test_llm_enhancement_candidates.py`, assert the returned value is a `WeaponLibraryCandidateReport` and use object attributes:

```python
assert isinstance(report, WeaponLibraryCandidateReport)
assert report.schema_version == "1.0"
assert report.source == "llm_scan_proposal"
assert {item.candidate_type for item in report.candidates} == {"guide", "sensor"}
assert all(item.status == "candidate" for item in report.candidates)
```

- [ ] **Step 5: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_weapon_library_candidate_report_rejects_invalid_status tests/unit/test_write_assets.py::test_llm_enhancement_candidates_returns_schema_report tests/unit/test_llm_enhancement_candidates.py tests/integration/test_benchmark_command.py::test_benchmark_fails_weapon_library_candidates_with_invalid_status -q
```

Expected: FAIL because the schema module does not exist and benchmark does not yet use it.

### Task 2: Implement Schema And Wire Generation

**Files:**
- Create: `src/harness_builder_agent/schemas/weapon_library_candidate.py`
- Modify: `src/harness_builder_agent/tools/llm_enhancement_candidates.py`
- Modify: `src/harness_builder_agent/tools/write_assets.py`
- Modify: `src/harness_builder_agent/tools/asset_writers/candidates.py`
- Modify: `src/harness_builder_agent/tools/interactive_init.py`

- [ ] **Step 1: Add schema module**

Create:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class WeaponLibraryCandidate(BaseModel):
    id: str
    candidate_type: Literal["guide", "sensor"]
    status: Literal["candidate", "confirmed", "rejected"]
    title: str
    rationale: str
    evidence: list[str] = Field(min_length=1)
    source: Literal["llm_scan_proposal"] = "llm_scan_proposal"
    human_confirmation_required: bool
    decision_notes: str | None = None


class WeaponLibraryCandidateReport(BaseModel):
    schema_version: str = "1.0"
    source: Literal["llm_scan_proposal"] = "llm_scan_proposal"
    candidates: list[WeaponLibraryCandidate] = Field(min_length=1)
```

- [ ] **Step 2: Return schema report from builder**

In `llm_enhancement_candidates.py`:

```python
from harness_builder_agent.schemas.weapon_library_candidate import WeaponLibraryCandidateReport
```

Change the return:

```python
return WeaponLibraryCandidateReport(candidates=candidates)
```

Update helper signatures to accept `WeaponLibraryCandidateReport | dict[str, Any]` only if needed; prefer `WeaponLibraryCandidateReport`.

- [ ] **Step 3: Update writer boundary**

In `write_assets.py`, convert the schema report to dict before applying decisions:

```python
raw_candidates = build_llm_enhancement_candidates(inventory, commands).model_dump(mode="json")
enhancement_candidates = apply_candidate_decisions(raw_candidates, decisions)
```

This preserves existing dict-based decision mutation.

- [ ] **Step 4: Validate candidate writer boundary**

In `src/harness_builder_agent/tools/asset_writers/candidates.py`, validate dict payloads before writing:

```python
enhancement_report = WeaponLibraryCandidateReport.model_validate(enhancement_candidates)
enhancement_payload = enhancement_report.model_dump(mode="json")
```

Use `enhancement_payload` for YAML and Markdown writers.

- [ ] **Step 5: Update guided init preview**

In `src/harness_builder_agent/tools/interactive_init.py`, replace dict `.get()` usage:

```python
candidate_ids = [item.id for item in candidate_report.candidates]
```

- [ ] **Step 6: Run generation-focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_weapon_library_candidate_report_rejects_invalid_status tests/unit/test_write_assets.py::test_llm_enhancement_candidates_returns_schema_report tests/unit/test_llm_enhancement_candidates.py tests/unit/test_asset_writer_candidates.py tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path -q
```

Expected: schema and writer tests pass.

### Task 3: Wire Benchmark Schema Validation

**Files:**
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `docs/engineering/init-workflow.md`

- [ ] **Step 1: Import schema**

Add:

```python
from harness_builder_agent.schemas.weapon_library_candidate import WeaponLibraryCandidateReport
```

- [ ] **Step 2: Replace ad hoc schema check**

In `_llm_enhancement_checks`, parse:

```python
report = WeaponLibraryCandidateReport.model_validate(yaml.safe_load(report_path.read_text(encoding="utf-8")))
candidates = report.candidates
checks = [{"id": "schema:weapon-library-candidates", "passed": True, "candidate_count": len(candidates)}]
```

On exception, keep the existing failed schema/content response.

Update content check:

```python
"passed": all(item.status == "candidate" and item.human_confirmation_required is True for item in candidates)
and "candidate" in review_text.lower(),
```

- [ ] **Step 3: Update engineering docs**

In `docs/engineering/init-workflow.md`, add that `.ai/experience/weapon-library-candidates.yaml` is validated by `WeaponLibraryCandidateReport`.

- [ ] **Step 4: Run benchmark-focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py::test_benchmark_fails_weapon_library_candidates_with_invalid_status tests/integration/test_benchmark_command.py::test_benchmark_generates_report_for_java_fixture -q
```

Expected: both tests pass.

### Task 4: Verify And Commit

**Files:**
- Create: `src/harness_builder_agent/schemas/weapon_library_candidate.py`
- Create: `docs/superpowers/specs/2026-05-31-weapon-library-candidate-schema-design.md`
- Create: `docs/superpowers/plans/2026-05-31-weapon-library-candidate-schema.md`
- Modify: `src/harness_builder_agent/tools/llm_enhancement_candidates.py`
- Modify: `src/harness_builder_agent/tools/write_assets.py`
- Modify: `src/harness_builder_agent/tools/asset_writers/candidates.py`
- Modify: `src/harness_builder_agent/tools/interactive_init.py`
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/unit/test_schema_contracts.py`
- Modify: `tests/unit/test_llm_enhancement_candidates.py`
- Modify: `tests/unit/test_write_assets.py`
- Modify: `tests/integration/test_benchmark_command.py`
- Modify: `docs/engineering/init-workflow.md`

- [ ] **Step 1: Run focused suite**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_enhancement_candidates.py tests/unit/test_schema_contracts.py tests/unit/test_write_assets.py tests/unit/test_asset_writer_candidates.py tests/integration/test_init_on_fixture_projects.py tests/integration/test_benchmark_command.py -q
```

Expected: focused schema/writer/benchmark suite passes.

- [ ] **Step 2: Run fast regression before commit**

Run:

```bash
scripts/test-fast.sh
```

Expected: fast suite passes.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/engineering/init-workflow.md docs/superpowers/specs/2026-05-31-weapon-library-candidate-schema-design.md docs/superpowers/plans/2026-05-31-weapon-library-candidate-schema.md src/harness_builder_agent/schemas/weapon_library_candidate.py src/harness_builder_agent/tools/llm_enhancement_candidates.py src/harness_builder_agent/tools/write_assets.py src/harness_builder_agent/tools/asset_writers/candidates.py src/harness_builder_agent/tools/interactive_init.py src/harness_builder_agent/tools/benchmark.py tests/unit/test_schema_contracts.py tests/unit/test_llm_enhancement_candidates.py tests/unit/test_write_assets.py tests/integration/test_benchmark_command.py
git commit -m "feat: validate weapon library candidates with schema"
```

- [ ] **Step 4: Run full regression and push**

Run:

```bash
scripts/test-full.sh
git push
scripts/check-ci.sh
```

Expected: local full suite passes before push, push succeeds, and CI status is checked after push.
