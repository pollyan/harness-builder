# Maturity-Driven Improve Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `harness-builder-agent improve` so improvement candidates are generated from structured maturity next steps, active blocking caps, and `.ai/maturity-evidence.yaml`.

**Architecture:** Extend the improvement candidate schema with optional traceability fields, then refactor `generate_improvements.py` to load both `MaturityReport` and `MaturityEvidencePack`. The generator remains deterministic and only writes candidate / pending-review assets.

**Tech Stack:** Python, Pydantic v2, PyYAML, pytest, current Typer integration tests.

---

## Files

- Modify: `src/harness_builder_agent/schemas/improvement_candidate.py`
- Modify: `src/harness_builder_agent/tools/generate_improvements.py`
- Modify: `tests/unit/test_schema_contracts.py`
- Modify: `tests/integration/test_assess_improve_commands.py`
- Modify: `docs/superpowers/plans/2026-05-31-maturity-driven-improve.md`

## Task 1: Candidate Schema Traceability

**Files:**
- Modify: `tests/unit/test_schema_contracts.py`
- Modify: `src/harness_builder_agent/schemas/improvement_candidate.py`

- [x] **Step 1: Write failing schema assertions**

Update `test_improvement_candidate_report_requires_reviewable_candidates` so the candidate payload includes traceability fields and the assertions read them:

```python
                    "target_dimension": "guides",
                    "source_next_step": "guides-bind-workflow",
                    "source_blocking_cap": None,
                    "acceptance_checks": ["Benchmark content:guides-quality passes."],
                    "evidence_sources": [".ai/maturity-evidence.yaml", ".ai/project-inventory.json"],
```

Add assertions:

```python
    assert report.candidates[0].target_dimension == "guides"
    assert report.candidates[0].source_next_step == "guides-bind-workflow"
    assert report.candidates[0].acceptance_checks == ["Benchmark content:guides-quality passes."]
    assert ".ai/maturity-evidence.yaml" in report.candidates[0].evidence_sources
```

- [x] **Step 2: Run schema test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_improvement_candidate_report_requires_reviewable_candidates -q
```

Expected: fail because `ImprovementCandidate` does not expose `target_dimension`.

- [x] **Step 3: Extend schema**

Add fields to `ImprovementCandidate`:

```python
    target_dimension: str | None = None
    source_next_step: str | None = None
    source_blocking_cap: str | None = None
    acceptance_checks: list[str] = Field(default_factory=list)
    evidence_sources: list[str] = Field(default_factory=list)
```

- [x] **Step 4: Run schema test and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_improvement_candidate_report_requires_reviewable_candidates -q
```

Expected: pass.

## Task 2: Improve Rebuilds Evidence and Emits Maturity-Linked Candidates

**Files:**
- Modify: `tests/integration/test_assess_improve_commands.py`
- Modify: `src/harness_builder_agent/tools/generate_improvements.py`

- [x] **Step 1: Write failing improve assertions**

In `test_improve_generates_reviewable_improvement_candidates`, delete the evidence pack after `assess`, then assert `improve` rebuilds it and emits maturity-linked candidate metadata:

```python
    (repo / ".ai" / "maturity-evidence.yaml").unlink()

    result = runner.invoke(app, ["improve", "--repo", str(repo)])
```

Add assertions after loading candidates:

```python
    assert (repo / ".ai" / "maturity-evidence.yaml").exists()
    assert first["target_dimension"]
    assert first["source_next_step"] or first["source_blocking_cap"]
    assert first["acceptance_checks"]
    assert ".ai/maturity-evidence.yaml" in first["evidence_sources"]
    assert "Acceptance checks" in pending
    assert "Maturity dimension" in evolution
```

- [x] **Step 2: Run improve test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_improve_generates_reviewable_improvement_candidates -q
```

Expected: fail because `improve` does not rebuild missing evidence and candidates lack traceability fields.

- [x] **Step 3: Load maturity evidence in improve**

In `generate_improvements.py`:

```python
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
```

Change the missing-file guard:

```python
    if not (ai / "maturity-score.yaml").exists() or not (ai / "maturity-evidence.yaml").exists():
        assess_maturity(root)
```

Load the evidence pack:

```python
    evidence_pack = MaturityEvidencePack.model_validate(yaml.safe_load((ai / "maturity-evidence.yaml").read_text(encoding="utf-8")))
    candidates = ImprovementCandidateReport(candidates=_candidates(score, evidence_pack))
```

- [x] **Step 4: Generate candidates from next steps, caps, and warnings**

Replace `_candidates(score)` with `_candidates(score, evidence_pack)`:

```python
def _candidates(score: MaturityReport, evidence_pack: MaturityEvidencePack) -> list[ImprovementCandidate]:
    candidates: list[ImprovementCandidate] = []
    seen: set[str] = set()
    for step in sorted(score.next_steps, key=_priority_rank):
        _append_unique(candidates, seen, _candidate_from_next_step(step, score, evidence_pack))
    for cap in score.blocking_caps:
        if cap.active:
            _append_unique(candidates, seen, _candidate_from_cap(cap, evidence_pack))
    for warning in evidence_pack.warnings:
        if "task-runs" in warning:
            _append_unique(candidates, seen, _runtime_evidence_candidate(warning, evidence_pack))
    return candidates
```

Add helper functions:

```python
def _priority_rank(step) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(step.priority, 3)


def _candidate_priority(priority: str) -> str:
    return "high" if priority in {"critical", "high"} else priority


def _append_unique(candidates: list[ImprovementCandidate], seen: set[str], candidate: ImprovementCandidate) -> None:
    if candidate.id not in seen:
        candidates.append(candidate)
        seen.add(candidate.id)
```

Implement mapping helpers:

```python
def _candidate_type_for_dimension(dimension: str) -> str:
    if dimension in {"guides"}:
        return "guide_update"
    if dimension in {"sensors", "verification_sophistication"}:
        return "sensor_update"
    if dimension in {"workflow", "repair_loop", "risk_control"}:
        return "workflow_policy_update"
    return "maturity_action"


def _target_for_dimension(dimension: str) -> str:
    return {
        "guides": ".ai/guides/project-context.md",
        "sensors": ".ai/sensors/verification.md",
        "verification_sophistication": ".ai/sensors/verification.md",
        "workflow": ".ai/harness-config.yaml",
        "repair_loop": ".ai/skills/bugfix/SKILL.md",
        "risk_control": ".ai/harness-config.yaml",
        "experience": ".ai/experience/pending-improvements.md",
        "observability": ".ai/runs/",
        "governance_auditability": ".ai/runs/",
    }.get(dimension, ".ai/maturity-report.md")
```

Use acceptance checks:

```python
def _acceptance_checks(dimension: str) -> list[str]:
    base = [f"Candidate remains pending review before formal {dimension} assets are changed."]
    if dimension == "guides":
        return base + ["Benchmark content:guides-quality passes."]
    if dimension in {"sensors", "verification_sophistication"}:
        return base + ["Benchmark content:sensors-quality and content:hard-gate-command-evidence pass."]
    if dimension in {"workflow", "repair_loop", "risk_control"}:
        return base + ["Benchmark content:workflow-skill-config-reference passes."]
    if dimension in {"observability", "governance_auditability"}:
        return base + ["Generation trace and maturity evidence remain schema-valid."]
    return base + ["maturity-score.yaml and maturity-evidence.yaml remain schema-valid."]
```

Create candidates:

```python
def _candidate_from_next_step(step, score: MaturityReport, evidence_pack: MaturityEvidencePack) -> ImprovementCandidate:
    dimension = step.target_dimension
    return ImprovementCandidate(
        id=f"maturity-next-step-{step.id}",
        candidate_type=_candidate_type_for_dimension(dimension),
        suggested_target=_target_for_dimension(dimension),
        rationale=f"{step.action} Expected maturity lift: {step.expected_lift or 'not specified'}.",
        evidence=_dimension_evidence(score, dimension) + evidence_pack.warnings,
        confidence="medium",
        priority=_candidate_priority(step.priority),
        target_dimension=dimension,
        source_next_step=step.id,
        acceptance_checks=_acceptance_checks(dimension),
        evidence_sources=_evidence_sources(evidence_pack),
    )
```

Caps:

```python
def _candidate_from_cap(cap, evidence_pack: MaturityEvidencePack) -> ImprovementCandidate:
    dimension = _dimension_for_cap(cap.id)
    return ImprovementCandidate(
        id=f"maturity-blocking-cap-{cap.id}",
        candidate_type=_candidate_type_for_dimension(dimension),
        suggested_target=_target_for_dimension(dimension),
        rationale=f"Active maturity cap `{cap.id}` limits the harness to {cap.max_level}: {cap.reason}",
        evidence=cap.evidence or evidence_pack.warnings,
        confidence="medium",
        priority="high",
        target_dimension=dimension,
        source_blocking_cap=cap.id,
        acceptance_checks=_acceptance_checks(dimension),
        evidence_sources=_evidence_sources(evidence_pack),
    )
```

- [x] **Step 5: Update Markdown writers**

Update `_write_evolution_plan` lines so each item includes:

```text
Maturity dimension: <dimension>
Acceptance checks: <joined checks>
```

Update `_write_pending_improvements` lines so each item includes the same two labels.

- [x] **Step 6: Run improve test and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_improve_generates_reviewable_improvement_candidates -q
```

Expected: pass.

## Task 3: Focused Verification

**Files:**
- All modified code and tests.

- [x] **Step 1: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py tests/integration/test_assess_improve_commands.py tests/integration/test_benchmark_command.py -q
```

Expected: pass.

- [x] **Step 2: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [x] **Step 3: Self-Harness Improvement Gate**

Check whether this milestone requires engineering docs or benchmark changes. Expected result: no engineering doc change is required because the existing architecture and init-workflow docs already define `improve`, candidate-only rule changes, schema validation, and benchmark validation for `improvement-candidates.yaml`.

- [x] **Step 4: Commit**

Run:

```bash
git add src/harness_builder_agent/schemas/improvement_candidate.py src/harness_builder_agent/tools/generate_improvements.py tests/unit/test_schema_contracts.py tests/integration/test_assess_improve_commands.py docs/superpowers/plans/2026-05-31-maturity-driven-improve.md
git commit -m "feat: make improve maturity driven"
```

Expected: commit succeeds after pre-commit fast regression.
