# Maturity Model v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand `maturity-score.yaml` from a flat POC scorecard into a structured, per-dimension roadmap contract.

**Architecture:** Keep the existing `MaturityReport` top-level summary fields for compatibility, then add nested dimension reports, blocking caps, typed next steps, and deterministic assessment helpers. `assess` and initial asset writing both emit schema-valid v2 maturity payloads; later milestones can layer LLM maturity review and maturity-driven improve on top.

**Tech Stack:** Python, Pydantic v2, PyYAML, pytest, existing CLI and asset writer patterns.

---

## Files

- Modify: `src/harness_builder_agent/schemas/maturity_report.py`
  - Add `MaturityLevel`, `MaturityEvidence`, `MaturityBlocker`, `MaturityNextStep`, `MaturityDimensionReport`, and `MaturityBlockingCap`.
  - Extend `MaturityReport` with `target_next_level`, `dimensions`, `blocking_caps`, and `next_steps`.
- Create: `src/harness_builder_agent/tools/maturity_model.py`
  - Central deterministic maturity builder shared by `assess` and initial asset writer.
- Modify: `src/harness_builder_agent/tools/assess_maturity.py`
  - Replace inline scoring with `build_maturity_report`.
  - Write Markdown with dimension details and next-level requirements.
- Modify: `src/harness_builder_agent/tools/asset_writers/reports.py`
  - Use `build_maturity_report` for initial `maturity-score.yaml`.
  - Keep initial `maturity-report.md` stable while adding dimension details.
- Modify: `tests/unit/test_schema_contracts.py`
  - Add schema test for structured maturity dimensions, blockers, caps, and next steps.
- Modify: `tests/unit/test_asset_writer_reports.py`
  - Assert initial writer emits v2 structured maturity score.
- Modify: `tests/integration/test_assess_improve_commands.py`
  - Assert `assess` emits all strategy dimensions, target next level, caps, dimension evidence, blockers, and Markdown sections.

## Task 1: Schema Contract

**Files:**
- Modify: `tests/unit/test_schema_contracts.py`
- Modify: `src/harness_builder_agent/schemas/maturity_report.py`

- [x] **Step 1: Write failing schema test**

Add to `tests/unit/test_schema_contracts.py`:

```python
def test_maturity_report_records_structured_dimension_roadmap():
    report = MaturityReport.model_validate(
        {
            "overall_level": "L2",
            "target_next_level": "L3",
            "dimension_scores": {"guides": "L2"},
            "dimensions": {
                "guides": {
                    "level": "L2",
                    "evidence": [{"source": ".ai/guides/project-context.md", "summary": "Structured project facts exist."}],
                    "blockers": [{"id": "guides-not-risk-routed", "reason": "Guides are not loaded by risk context.", "prevents_level": "L3"}],
                    "next_level_requirements": ["Bind guides to workflow routing."],
                    "confidence": "high",
                }
            },
            "blocking_caps": [
                {
                    "id": "no-runtime-audit",
                    "reason": "No runtime audit events were found.",
                    "max_level": "L3",
                    "active": True,
                    "evidence": [".ai/task-runs absent"],
                }
            ],
            "next_steps": [
                {
                    "id": "bind-guides-to-workflow",
                    "target_dimension": "guides",
                    "action": "Bind project guides to workflow routing.",
                    "priority": "high",
                    "expected_lift": "guides L2 -> L3",
                }
            ],
            "evidence": ["summary"],
            "blocking_reasons": ["blocker"],
            "recommended_next_steps": ["next"],
        }
    )

    assert report.target_next_level == "L3"
    assert report.dimensions["guides"].evidence[0].source == ".ai/guides/project-context.md"
    assert report.dimensions["guides"].blockers[0].prevents_level == "L3"
    assert report.blocking_caps[0].active is True
    assert report.next_steps[0].target_dimension == "guides"
```

- [x] **Step 2: Run schema test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_maturity_report_records_structured_dimension_roadmap -q
```

Expected: fail because `MaturityReport` does not have the new fields yet.

- [x] **Step 3: Implement schema models**

Replace `src/harness_builder_agent/schemas/maturity_report.py` with the expanded schema:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from harness_builder_agent.schemas.common import Confidence

MaturityLevel = Literal["L0", "L1", "L2", "L3", "L4"]


class MaturityEvidence(BaseModel):
    source: str
    summary: str


class MaturityBlocker(BaseModel):
    id: str
    reason: str
    prevents_level: MaturityLevel | None = None


class MaturityNextStep(BaseModel):
    id: str
    target_dimension: str
    action: str
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    expected_lift: str | None = None


class MaturityDimensionReport(BaseModel):
    level: MaturityLevel
    evidence: list[MaturityEvidence] = Field(default_factory=list)
    blockers: list[MaturityBlocker] = Field(default_factory=list)
    next_level_requirements: list[str] = Field(default_factory=list)
    confidence: Confidence = "medium"


class MaturityBlockingCap(BaseModel):
    id: str
    reason: str
    max_level: MaturityLevel
    active: bool = True
    evidence: list[str] = Field(default_factory=list)


class MaturityReport(BaseModel):
    schema_version: str = "1.0"
    overall_level: MaturityLevel = "L1"
    target_next_level: MaturityLevel | None = None
    dimension_scores: dict[str, MaturityLevel] = Field(default_factory=dict)
    dimensions: dict[str, MaturityDimensionReport] = Field(default_factory=dict)
    blocking_caps: list[MaturityBlockingCap] = Field(default_factory=list)
    next_steps: list[MaturityNextStep] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    last_assessed_at: str | None = None
```

- [x] **Step 4: Run schema tests and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_maturity_report_records_structured_dimension_roadmap tests/unit/test_schema_contracts.py::test_maturity_report_records_scores_evidence_and_next_steps -q
```

Expected: pass.

## Task 2: Deterministic Maturity Builder

**Files:**
- Create: `src/harness_builder_agent/tools/maturity_model.py`
- Modify: `tests/integration/test_assess_improve_commands.py`

- [x] **Step 1: Write failing assess integration assertions**

Extend `test_assess_generates_maturity_score_from_current_harness`:

```python
    expected_dimensions = {
        "guides",
        "sensors",
        "workflow",
        "risk_control",
        "repair_loop",
        "observability",
        "experience",
        "verification_sophistication",
        "governance_auditability",
    }
    assert set(score["dimensions"]) == expected_dimensions
    assert score["target_next_level"] == "L3"
    assert score["dimensions"]["guides"]["evidence"]
    assert score["dimensions"]["sensors"]["next_level_requirements"]
    assert score["next_steps"]
```

Extend `test_assess_handles_empty_command_catalog_by_lowering_sensor_maturity`:

```python
    assert score["dimensions"]["sensors"]["level"] == "L0"
    assert any(cap["id"] == "no-executable-sensors" and cap["active"] for cap in score["blocking_caps"])
    assert any(step["target_dimension"] == "sensors" for step in score["next_steps"])
```

- [x] **Step 2: Run integration tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_assess_generates_maturity_score_from_current_harness tests/integration/test_assess_improve_commands.py::test_assess_handles_empty_command_catalog_by_lowering_sensor_maturity -q
```

Expected: fail because `dimensions`, `blocking_caps`, and `next_steps` are absent.

- [x] **Step 3: Implement `build_maturity_report`**

Create `src/harness_builder_agent/tools/maturity_model.py` with deterministic dimension construction. The implementation should:

- Build all nine strategy dimensions.
- Keep `dimension_scores` in sync with `dimensions`.
- Add active `no-executable-sensors` cap when command catalog is empty.
- Add `runtime-audit-not-owned-by-builder` cap as active above L3 because Runtime evidence is external.
- Set `target_next_level` to the next level after `overall_level` when possible.
- Return a `MaturityReport`.

- [x] **Step 4: Wire `assess_maturity` to builder**

Modify `src/harness_builder_agent/tools/assess_maturity.py`:

```python
from harness_builder_agent.tools.maturity_model import build_maturity_report
```

Replace inline `MaturityReport(...)` construction with:

```python
score = build_maturity_report(ai, inventory, commands, config, assessed_at=datetime.now(UTC).isoformat())
```

- [x] **Step 5: Update Markdown report writer**

Update `_write_report` to include:

```markdown
## 维度详情

- guides: L2
  - evidence...
  - blockers...

## 下一等级要求
```

- [x] **Step 6: Run focused integration tests and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_assess_generates_maturity_score_from_current_harness tests/integration/test_assess_improve_commands.py::test_assess_handles_empty_command_catalog_by_lowering_sensor_maturity -q
```

Expected: pass.

## Task 3: Initial Asset Writer Uses v2 Score

**Files:**
- Modify: `src/harness_builder_agent/tools/asset_writers/reports.py`
- Modify: `tests/unit/test_asset_writer_reports.py`

- [x] **Step 1: Write failing initial writer assertions**

In `tests/unit/test_asset_writer_reports.py`, extend the maturity score test:

```python
    maturity = yaml.safe_load((ai / "maturity-score.yaml").read_text(encoding="utf-8"))
    assert "dimensions" in maturity
    assert "guides" in maturity["dimensions"]
    assert maturity["dimensions"]["workflow"]["next_level_requirements"]
    assert "next_steps" in maturity
```

- [x] **Step 2: Run unit test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_reports.py -q
```

Expected: fail because initial writer still writes flat maturity score.

- [x] **Step 3: Wire asset writer to builder**

Modify `src/harness_builder_agent/tools/asset_writers/reports.py`:

```python
from harness_builder_agent.tools.maturity_model import build_maturity_report
```

Replace `_maturity_score(...)` internals with:

```python
return build_maturity_report(
    ai=None,
    inventory=inventory,
    commands=commands,
    config=config,
    weapon_selection=weapon_selection,
).model_dump(mode="json")
```

Update `_maturity_report(...)` to render the structured `MaturityReport`.

- [x] **Step 4: Run asset writer test and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_reports.py -q
```

Expected: pass.

## Task 4: Regression and Commit

**Files:**
- All modified source and tests.

- [x] **Step 1: Run focused maturity tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py tests/unit/test_asset_writer_reports.py tests/integration/test_assess_improve_commands.py -q
```

Expected: pass.

- [x] **Step 2: Run default fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [x] **Step 3: Commit implementation**

Run:

```bash
git add src/harness_builder_agent/schemas/maturity_report.py src/harness_builder_agent/tools/maturity_model.py src/harness_builder_agent/tools/assess_maturity.py src/harness_builder_agent/tools/asset_writers/reports.py tests/unit/test_schema_contracts.py tests/unit/test_asset_writer_reports.py tests/integration/test_assess_improve_commands.py docs/superpowers/plans/2026-05-31-maturity-model-v2.md
git commit -m "feat: add maturity model v2 roadmap contract"
```

Expected: commit succeeds after pre-commit fast regression.
