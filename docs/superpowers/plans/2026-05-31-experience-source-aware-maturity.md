# Experience Source Aware Maturity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make the Experience maturity dimension consume `experience-index.yaml` review source counts, including workflow recommendation reviews.

**Architecture:** Add focused unit tests for `build_maturity_report`, then update `_experience_dimension` to read `ExperienceIndex` when available. The change is deterministic and additive; legacy directories without an index keep the existing pending-file path.

**Tech Stack:** Python, Pydantic, YAML, pytest.

---

### Task 1: Add failing maturity model tests

**Files:**
- Create: `tests/unit/test_maturity_model.py`

- [x] **Step 1: Add test helpers and source-aware Experience test**

Create:

```python
from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.maturity_model import build_maturity_report


def _inventory() -> ProjectInventory:
    return ProjectInventory(repo_name="demo", root_path="/tmp/demo", primary_stack="java-spring", modules=[], evidence=[])


def _commands() -> CommandCatalog:
    return CommandCatalog(commands=[])


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_experience_dimension_uses_workflow_recommendation_review_count(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_yaml(
        ai / "experience" / "experience-index.yaml",
        {
            "schema_version": "1.0",
            "experience_files": {"pending-improvements.md": True},
            "sources": [
                {"path": ".ai/review/workflow-routing-recommendation.yaml", "kind": "workflow_recommendation", "item_count": 1}
            ],
            "pending_improvement_count": 0,
            "asset_candidate_count": 0,
            "maturity_review_count": 0,
            "workflow_recommendation_count": 1,
            "runtime_task_run_count": 0,
            "warnings": [],
        },
    )

    report = build_maturity_report(ai=ai, inventory=_inventory(), commands=_commands(), config=HarnessConfig.default())

    experience = report.dimensions["experience"]
    assert experience.level == "L2"
    assert any("Workflow recommendation reviews: 1" in item.summary for item in experience.evidence)
    assert any(blocker.id == "experience-not-runtime-derived" for blocker in experience.blockers)
```

- [x] **Step 2: Add legacy compatibility test**

Add:

```python
def test_experience_dimension_keeps_legacy_pending_file_behavior(tmp_path: Path):
    ai = tmp_path / ".ai"
    (ai / "experience").mkdir(parents=True)
    (ai / "experience" / "pending-improvements.md").write_text("# Pending Improvements\n", encoding="utf-8")

    report = build_maturity_report(ai=ai, inventory=_inventory(), commands=_commands(), config=HarnessConfig.default())

    assert report.dimensions["experience"].level == "L1"
```

- [x] **Step 3: Run focused tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_maturity_model.py -q
```

Expected: source-aware test fails because Experience dimension still ignores `experience-index.yaml`.

### Task 2: Implement source-aware Experience dimension

**Files:**
- Modify: `src/harness_builder_agent/tools/maturity_model.py`

- [x] **Step 1: Import YAML and schema**

Add:

```python
import yaml
from harness_builder_agent.schemas.experience_index import ExperienceIndex
```

- [x] **Step 2: Read index in `_experience_dimension`**

Replace the current implementation with logic that:

```python
index_path = ai / "experience" / "experience-index.yaml"
if ai is not None and index_path.exists():
    index = ExperienceIndex.model_validate(yaml.safe_load(index_path.read_text(encoding="utf-8")))
    signal_count = (
        index.pending_improvement_count
        + index.asset_candidate_count
        + index.maturity_review_count
        + index.workflow_recommendation_count
        + index.runtime_task_run_count
    )
    level = "L2" if signal_count else "L1"
    evidence = [...]
```

Keep legacy pending-file behavior when the index is absent.

- [x] **Step 3: Run focused tests and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_maturity_model.py -q
```

Expected: pass.

### Task 3: Update docs and verify

**Files:**
- Modify: `docs/engineering/init-workflow.md`

- [x] **Step 1: Document source-aware maturity scoring**

Add a sentence that maturity scoring uses `experience-index.yaml` counts when present, including workflow recommendation review count.

- [x] **Step 2: Run references check**

Run:

```bash
rg -n "workflow recommendation review|workflow_recommendation_count|Experience dimension" docs/engineering src tests
```

Expected: docs, maturity model, schema, and tests are referenced.

### Task 4: Verify and commit

- [x] **Step 1: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_maturity_model.py tests/unit/test_maturity_evidence.py tests/unit/test_experience_index.py -q
```

Expected: pass.

- [x] **Step 2: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [x] **Step 3: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-05-31-experience-source-aware-maturity-design.md docs/superpowers/plans/2026-05-31-experience-source-aware-maturity.md tests/unit/test_maturity_model.py src/harness_builder_agent/tools/maturity_model.py docs/engineering/init-workflow.md
git commit -m "feat: score experience maturity from indexed sources"
```

Expected: commit succeeds after pre-commit fast test.

### Self-Review

- Spec coverage: source-aware scoring, workflow recommendation review signal, legacy compatibility, docs, and verification are covered.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: count names match `ExperienceIndex`.
