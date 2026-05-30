# Experience-aware Maturity Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Feed `.ai/experience/experience-index.yaml` into `.ai/maturity-evidence.yaml` so maturity review and improve flows can see reviewed candidates, generated asset drafts, and host Runtime task-run availability.

**Architecture:** Extend the maturity evidence schema with Experience Index-derived counters while preserving existing pending-improvement fields. Update the collector to validate and consume `ExperienceIndex` when present, with a legacy pending-only path for old generated Harness folders.

**Tech Stack:** Python, Pydantic v2, PyYAML, pytest.

---

## Files

- Modify: `src/harness_builder_agent/schemas/maturity_evidence.py`
- Modify: `src/harness_builder_agent/tools/maturity_evidence.py`
- Modify: `tests/unit/test_schema_contracts.py`
- Add: `tests/unit/test_maturity_evidence.py`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/superpowers/plans/2026-05-31-experience-aware-maturity-evidence.md`

## Task 1: Schema Contract

- [x] **Step 1: Write failing schema assertion**

In `tests/unit/test_schema_contracts.py`, update `test_maturity_evidence_pack_records_harness_inputs_for_review` so the `experience` payload includes:

```python
"experience": {
    "has_pending_improvements": True,
    "pending_improvement_count": 2,
    "has_experience_index": True,
    "asset_candidate_count": 1,
    "maturity_review_count": 1,
    "runtime_task_run_count": 0,
    "experience_file_count": 6,
},
```

Add assertions:

```python
assert pack.experience.has_experience_index is True
assert pack.experience.asset_candidate_count == 1
assert pack.experience.experience_file_count == 6
```

- [x] **Step 2: Run schema test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_maturity_evidence_pack_records_harness_inputs_for_review -q
```

Expected: fail because `ExperienceEvidence` does not expose the new fields.

- [x] **Step 3: Extend schema**

In `src/harness_builder_agent/schemas/maturity_evidence.py`, change `ExperienceEvidence` to:

```python
class ExperienceEvidence(BaseModel):
    has_pending_improvements: bool = False
    pending_improvement_count: int = 0
    has_experience_index: bool = False
    asset_candidate_count: int = 0
    maturity_review_count: int = 0
    runtime_task_run_count: int = 0
    experience_file_count: int = 0
```

- [x] **Step 4: Run schema test and confirm pass**

Run the same pytest command. Expected: pass.

## Task 2: Index-backed Collection

- [x] **Step 1: Write failing collector tests**

Create `tests/unit/test_maturity_evidence.py` with helpers that write minimal required schema files and two tests:

```python
from pathlib import Path

import yaml

from harness_builder_agent.tools.maturity_evidence import MATURITY_INPUTS, collect_maturity_evidence


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_base_ai(ai: Path) -> None:
    (ai / "project-inventory.json").write_text(
        '{"schema_version":"1.0","repo_name":"demo","root_path":"/tmp/demo","primary_stack":"java-spring","modules":[],"risk_areas":[],"evidence":[]}',
        encoding="utf-8",
    )
    _write_yaml(ai / "command-catalog.yaml", {"schema_version": "1.0", "commands": []})
    _write_yaml(ai / "harness-config.yaml", {"schema_version": "1.0", "workflows": {}})
    _write_yaml(
        ai / "weapon-library-selection.yaml",
        {
            "schema_version": "1.0",
            "primary_stack": "java-spring",
            "included_libraries": ["common"],
            "guide_weapon_ids": [],
            "sensor_weapon_ids": [],
            "workflow_weapon_ids": [],
            "selection_reasons": [],
            "missing_recommendations": [],
        },
    )


def test_collect_maturity_evidence_uses_experience_index(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_base_ai(ai)
    _write_yaml(
        ai / "experience" / "experience-index.yaml",
        {
            "schema_version": "1.0",
            "experience_files": {
                "project-experience.md": True,
                "repair-patterns.md": True,
                "sensor-feedback.md": True,
                "team-preferences.md": True,
                "pending-improvements.md": True,
                "deprecated-experience.md": False,
            },
            "pending_improvement_count": 2,
            "asset_candidate_count": 3,
            "maturity_review_count": 1,
            "runtime_task_run_count": 4,
            "warnings": [],
        },
    )

    pack = collect_maturity_evidence(ai)

    assert ".ai/experience/experience-index.yaml" in pack.maturity_inputs
    assert pack.experience.has_experience_index is True
    assert pack.experience.pending_improvement_count == 2
    assert pack.experience.asset_candidate_count == 3
    assert pack.experience.maturity_review_count == 1
    assert pack.experience.runtime_task_run_count == 4
    assert pack.experience.experience_file_count == 5


def test_collect_maturity_evidence_keeps_pending_only_legacy_path(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_base_ai(ai)
    (ai / "experience").mkdir(parents=True)
    (ai / "experience" / "pending-improvements.md").write_text(
        "# Pending Improvements\n\n- first\n- second\n",
        encoding="utf-8",
    )

    pack = collect_maturity_evidence(ai)

    assert pack.experience.has_experience_index is False
    assert pack.experience.has_pending_improvements is True
    assert pack.experience.pending_improvement_count == 2
    assert pack.experience.asset_candidate_count == 0
```

- [x] **Step 2: Run collector tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_maturity_evidence.py -q
```

Expected: fail because the collector ignores `experience-index.yaml`.

- [x] **Step 3: Implement index-backed collection**

In `src/harness_builder_agent/tools/maturity_evidence.py`:

1. Import `ExperienceIndex`.
2. Add `.ai/experience/experience-index.yaml` to `MATURITY_INPUTS`.
3. Update `_experience(ai)` to validate and consume the index if present:

```python
def _experience(ai: Path) -> ExperienceEvidence:
    index_path = ai / "experience" / "experience-index.yaml"
    if index_path.exists():
        index = ExperienceIndex.model_validate(yaml.safe_load(index_path.read_text(encoding="utf-8")))
        experience_file_count = sum(1 for exists in index.experience_files.values() if exists)
        return ExperienceEvidence(
            has_pending_improvements=index.pending_improvement_count > 0,
            pending_improvement_count=index.pending_improvement_count,
            has_experience_index=True,
            asset_candidate_count=index.asset_candidate_count,
            maturity_review_count=index.maturity_review_count,
            runtime_task_run_count=index.runtime_task_run_count,
            experience_file_count=experience_file_count,
        )
    pending = ai / "experience" / "pending-improvements.md"
    if not pending.exists():
        return ExperienceEvidence()
    text = pending.read_text(encoding="utf-8")
    count = sum(1 for line in text.splitlines() if line.lstrip().startswith("- "))
    return ExperienceEvidence(has_pending_improvements=count > 0, pending_improvement_count=count)
```

- [x] **Step 4: Run collector tests and confirm pass**

Run the same pytest command. Expected: pass.

## Task 3: Docs, Verification, Commit

- [x] **Step 1: Update engineering doc**

In `docs/engineering/init-workflow.md`, update the `maturity-evidence.yaml` paragraph to state that Experience evidence consumes `experience-index.yaml` when present and retains a legacy pending-only path when absent.

- [x] **Step 2: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py tests/unit/test_maturity_evidence.py tests/integration/test_assess_improve_commands.py -q
```

Expected: pass.

- [x] **Step 3: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [x] **Step 4: Self-Harness Improvement Gate**

Record whether this milestone needs benchmark, fixture, acceptance, docs/todos, or engineering-rule updates. Expected: schema and collector tests cover the contract; benchmark is indirectly covered through existing maturity-evidence schema validation.

Gate conclusion:

- Schema coverage was updated for the expanded `ExperienceEvidence` contract.
- Collector tests cover both index-backed and legacy pending-only paths.
- `docs/engineering/init-workflow.md` now records how maturity evidence consumes Experience Index.
- No new benchmark check is needed in this milestone because existing benchmark schema validation already validates `.ai/maturity-evidence.yaml`; this milestone changes the contents of that schema contract and is covered by focused schema/collector tests plus fast regression.
- No `docs/todos` entry is needed; the next candidate gap remains semantic Experience summarization or Workflow Toolkit evolution.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/harness_builder_agent/schemas/maturity_evidence.py src/harness_builder_agent/tools/maturity_evidence.py tests/unit/test_schema_contracts.py tests/unit/test_maturity_evidence.py docs/engineering/init-workflow.md docs/superpowers/specs/2026-05-31-experience-aware-maturity-evidence-design.md docs/superpowers/plans/2026-05-31-experience-aware-maturity-evidence.md
git commit -m "feat: feed experience index into maturity evidence"
```

Expected: commit succeeds after pre-commit fast regression.
