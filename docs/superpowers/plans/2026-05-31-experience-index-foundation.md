# Experience Index Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a schema-validated `.ai/experience/experience-index.yaml` and ensure the first-stage Experience Markdown files exist without overwriting customer edits.

**Architecture:** Add an Experience index schema and deterministic writer module. Wire the writer into initial asset generation, `improve`, and `generate-asset-candidates`, then make benchmark validate the new machine-consumed index.

**Tech Stack:** Python, Pydantic v2, PyYAML, pytest, current asset writer and benchmark patterns.

---

## Files

- Create: `src/harness_builder_agent/schemas/experience_index.py`
- Create: `src/harness_builder_agent/tools/experience_index.py`
- Modify: `src/harness_builder_agent/tools/asset_writers/candidates.py`
- Modify: `src/harness_builder_agent/tools/generate_improvements.py`
- Modify: `src/harness_builder_agent/tools/generate_asset_candidates.py`
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/unit/test_schema_contracts.py`
- Modify: `tests/unit/test_asset_writer_candidates.py`
- Modify: `tests/integration/test_assess_improve_commands.py`
- Modify: `tests/integration/test_benchmark_command.py`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/superpowers/plans/2026-05-31-experience-index-foundation.md`

## Task 1: Experience Index Schema

- [ ] **Step 1: Write failing schema tests**

In `tests/unit/test_schema_contracts.py`, import `ExperienceIndex` and add:

```python
def test_experience_index_records_sources_and_counts():
    index = ExperienceIndex.model_validate(
        {
            "experience_files": {
                "project-experience.md": True,
                "repair-patterns.md": True,
                "sensor-feedback.md": True,
                "team-preferences.md": True,
                "pending-improvements.md": True,
                "deprecated-experience.md": True,
            },
            "sources": [
                {"path": ".ai/experience/pending-improvements.md", "kind": "pending_improvements", "item_count": 2}
            ],
            "pending_improvement_count": 2,
            "asset_candidate_count": 1,
            "maturity_review_count": 1,
            "runtime_task_run_count": 0,
            "warnings": ["runtime task-runs absent"],
        }
    )

    assert index.schema_version == "1.0"
    assert index.sources[0].kind == "pending_improvements"
```

- [ ] **Step 2: Run schema test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_experience_index_records_sources_and_counts -q
```

Expected: fail because `experience_index.py` does not exist.

- [ ] **Step 3: Implement schema**

Create `src/harness_builder_agent/schemas/experience_index.py`:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ExperienceSource(BaseModel):
    path: str
    kind: Literal["pending_improvements", "maturity_review", "asset_candidates", "runtime_task_runs", "manual_experience"]
    item_count: int = 0


class ExperienceIndex(BaseModel):
    schema_version: str = "1.0"
    experience_files: dict[str, bool] = Field(default_factory=dict)
    sources: list[ExperienceSource] = Field(default_factory=list)
    pending_improvement_count: int = 0
    asset_candidate_count: int = 0
    maturity_review_count: int = 0
    runtime_task_run_count: int = 0
    warnings: list[str] = Field(default_factory=list)
```

- [ ] **Step 4: Run schema test and confirm pass**

Run the same pytest command. Expected: pass.

## Task 2: Writer and Initial Assets

- [ ] **Step 1: Write failing asset writer assertions**

In `tests/unit/test_asset_writer_candidates.py`, assert:

```python
    for name in [
        "project-experience.md",
        "repair-patterns.md",
        "sensor-feedback.md",
        "team-preferences.md",
        "deprecated-experience.md",
        "experience-index.yaml",
    ]:
        assert (ai / "experience" / name).exists()
    index = yaml.safe_load((ai / "experience" / "experience-index.yaml").read_text(encoding="utf-8"))
    assert index["schema_version"] == "1.0"
    assert index["pending_improvement_count"] == 0
    assert {"path": ".ai/experience/experience-index.yaml", "kind": "experience_index"} in artifacts["artifacts"]
```

- [ ] **Step 2: Run asset writer test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_candidates.py -q
```

Expected: fail because index/files are not written.

- [ ] **Step 3: Implement experience writer**

Create `src/harness_builder_agent/tools/experience_index.py` with:

- `EXPERIENCE_FILES` mapping filename to default heading/body.
- `ensure_experience_files(ai)` creates missing files only.
- `build_experience_index(ai)` counts pending bullets, asset candidates, maturity reviews, runtime task dirs.
- `write_experience_index(ai, trace=None)` writes YAML and records artifact.

- [ ] **Step 4: Wire candidate writer**

In `asset_writers/candidates.py`, call:

```python
ensure_experience_files(ai)
write_experience_index(ai, trace=trace)
```

after writing initial candidate assets.

- [ ] **Step 5: Run asset writer test and confirm pass**

Run the same pytest command. Expected: pass.

## Task 3: Refresh From Improve, Asset Candidates, Benchmark

- [ ] **Step 1: Write failing integration and benchmark assertions**

In `test_improve_generates_reviewable_improvement_candidates`, assert:

```python
    experience_index = yaml.safe_load((repo / ".ai" / "experience" / "experience-index.yaml").read_text(encoding="utf-8"))
    assert experience_index["pending_improvement_count"] >= 1
```

In `test_generate_asset_candidates_writes_review_only_drafts`, assert:

```python
    experience_index = yaml.safe_load((repo / ".ai" / "experience" / "experience-index.yaml").read_text(encoding="utf-8"))
    assert experience_index["asset_candidate_count"] == 1
```

In benchmark integration, assert `"schema:experience-index"` is present.

- [ ] **Step 2: Run focused failing tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_improve_generates_reviewable_improvement_candidates tests/integration/test_assess_improve_commands.py::test_generate_asset_candidates_writes_review_only_drafts tests/integration/test_benchmark_command.py::test_benchmark_generates_report_for_java_fixture -q
```

Expected: fail until refresh and benchmark validation are wired.

- [ ] **Step 3: Wire refresh**

Call `write_experience_index(ai)` after writing pending improvements in `generate_improvements.py` and after writing asset candidates in `generate_asset_candidates.py`.

- [ ] **Step 4: Wire benchmark**

In `benchmark.py`, add `experience/experience-index.yaml` to `REQUIRED_FILES`, import `ExperienceIndex`, validate it in `_schema_checks`, and add test assertion.

- [ ] **Step 5: Run focused tests and confirm pass**

Run the same focused command. Expected: pass.

## Task 4: Verification and Commit

- [ ] **Step 1: Update engineering doc**

Add `.ai/experience/experience-index.yaml` and the expanded Experience Markdown files to `docs/engineering/init-workflow.md`.

- [ ] **Step 2: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py tests/unit/test_asset_writer_candidates.py tests/integration/test_assess_improve_commands.py tests/integration/test_benchmark_command.py -q
```

Expected: pass.

- [ ] **Step 3: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [ ] **Step 4: Self-Harness Improvement Gate**

Expected result: schema, asset writer, integration, benchmark, and init workflow doc all cover the new Experience index contract.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/harness_builder_agent/schemas/experience_index.py src/harness_builder_agent/tools/experience_index.py src/harness_builder_agent/tools/asset_writers/candidates.py src/harness_builder_agent/tools/generate_improvements.py src/harness_builder_agent/tools/generate_asset_candidates.py src/harness_builder_agent/tools/benchmark.py tests/unit/test_schema_contracts.py tests/unit/test_asset_writer_candidates.py tests/integration/test_assess_improve_commands.py tests/integration/test_benchmark_command.py docs/engineering/init-workflow.md docs/superpowers/plans/2026-05-31-experience-index-foundation.md
git commit -m "feat: add experience index foundation"
```

Expected: commit succeeds after pre-commit fast regression.
