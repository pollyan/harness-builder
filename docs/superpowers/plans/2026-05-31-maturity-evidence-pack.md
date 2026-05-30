# Maturity Evidence Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `.ai/maturity-evidence.yaml` as a deterministic, schema-validated evidence pack for maturity assessment, future LLM maturity review, and maturity-driven improve.

**Architecture:** Add a schema in `schemas/`, a collector/writer in `tools/maturity_evidence.py`, then wire it into initial asset writing, `assess`, and benchmark schema validation. The pack summarizes current `.ai` state without copying large file contents and treats `.ai/task-runs` as optional host Runtime evidence.

**Tech Stack:** Python, Pydantic v2, PyYAML, pytest, current asset writer and benchmark patterns.

---

## Files

- Create: `src/harness_builder_agent/schemas/maturity_evidence.py`
- Create: `src/harness_builder_agent/tools/maturity_evidence.py`
- Modify: `src/harness_builder_agent/tools/asset_writers/reports.py`
- Modify: `src/harness_builder_agent/tools/assess_maturity.py`
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `src/harness_builder_agent/cli.py`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `tests/unit/test_schema_contracts.py`
- Modify: `tests/unit/test_asset_writer_reports.py`
- Modify: `tests/integration/test_assess_improve_commands.py`
- Modify: `tests/integration/test_benchmark_command.py`

## Task 1: Schema Contract

**Files:**
- Modify: `tests/unit/test_schema_contracts.py`
- Create: `src/harness_builder_agent/schemas/maturity_evidence.py`

- [x] **Step 1: Write failing schema test**

Add to `tests/unit/test_schema_contracts.py`:

```python
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack


def test_maturity_evidence_pack_records_harness_inputs_for_review():
    pack = MaturityEvidencePack.model_validate(
        {
            "repo_name": "demo",
            "primary_stack": "java-spring",
            "inventory_summary": {"module_count": 2, "evidence_count": 3, "risk_area_count": 1},
            "command_summary": {"total_count": 2, "hard_gate_count": 1, "soft_gate_count": 1, "command_ids": ["unit_test"]},
            "harness_assets": {
                "guide_count": 3,
                "sensor_count": 2,
                "workflow_skill_count": 2,
                "has_harness_config": True,
                "has_weapon_library_selection": True,
            },
            "observability": {
                "generation_run_count": 1,
                "has_runtime_task_runs": False,
                "latest_generation_status": "completed",
            },
            "experience": {"has_pending_improvements": True, "pending_improvement_count": 2},
            "benchmark": {"has_report": True, "status": "passed"},
            "maturity_inputs": [".ai/project-inventory.json", ".ai/command-catalog.yaml"],
            "warnings": ["runtime task-runs absent"],
        }
    )

    assert pack.schema_version == "1.0"
    assert pack.command_summary.hard_gate_count == 1
    assert pack.observability.has_runtime_task_runs is False
```

- [x] **Step 2: Run schema test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_maturity_evidence_pack_records_harness_inputs_for_review -q
```

Expected: fail because `MaturityEvidencePack` does not exist.

- [x] **Step 3: Implement schema**

Create `src/harness_builder_agent/schemas/maturity_evidence.py` with Pydantic models:

```python
InventoryEvidenceSummary
CommandEvidenceSummary
HarnessAssetEvidence
ObservabilityEvidence
ExperienceEvidence
BenchmarkEvidence
MaturityEvidencePack
```

- [x] **Step 4: Run schema test and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_maturity_evidence_pack_records_harness_inputs_for_review -q
```

Expected: pass.

## Task 2: Evidence Collector and Asset Writer

**Files:**
- Create: `src/harness_builder_agent/tools/maturity_evidence.py`
- Modify: `src/harness_builder_agent/tools/asset_writers/reports.py`
- Modify: `tests/unit/test_asset_writer_reports.py`

- [x] **Step 1: Write failing asset writer assertions**

Extend `test_write_report_assets_writes_reports_scores_plan_and_records_trace`:

```python
    assert (ai / "maturity-evidence.yaml").exists()
    evidence = yaml.safe_load((ai / "maturity-evidence.yaml").read_text(encoding="utf-8"))
    assert evidence["schema_version"] == "1.0"
    assert evidence["repo_name"] == tmp_path.name
    assert evidence["command_summary"]["hard_gate_count"] == 1
    assert ".ai/project-inventory.json" in evidence["maturity_inputs"]
    assert {"path": ".ai/maturity-evidence.yaml", "kind": "maturity_evidence"} in artifacts["artifacts"]
```

- [x] **Step 2: Run asset writer test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_reports.py -q
```

Expected: fail because the file is not written.

- [x] **Step 3: Implement collector**

Create `build_maturity_evidence_pack(...)` for in-memory initial generation and `collect_maturity_evidence(ai, ...)` for disk refresh.

- [x] **Step 4: Wire report asset writer**

In `write_report_assets`, write `.ai/maturity-evidence.yaml` and record artifact kind `maturity_evidence`.

- [x] **Step 5: Run asset writer test and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_reports.py -q
```

Expected: pass.

## Task 3: Assess Refreshes Evidence Pack

**Files:**
- Modify: `src/harness_builder_agent/tools/assess_maturity.py`
- Modify: `tests/integration/test_assess_improve_commands.py`

- [x] **Step 1: Write failing assess assertions**

Extend `test_assess_generates_maturity_score_from_current_harness`:

```python
    evidence_pack = yaml.safe_load((repo / ".ai" / "maturity-evidence.yaml").read_text(encoding="utf-8"))
    assert evidence_pack["primary_stack"] == "java-spring"
    assert evidence_pack["harness_assets"]["workflow_skill_count"] == 2
    assert evidence_pack["observability"]["generation_run_count"] >= 1
```

- [x] **Step 2: Run assess test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_assess_generates_maturity_score_from_current_harness -q
```

Expected: fail because assess does not refresh the evidence pack.

- [x] **Step 3: Wire assess**

In `assess_maturity`, call `collect_maturity_evidence(...)`, write `.ai/maturity-evidence.yaml`, and keep the command trace artifact.

- [x] **Step 4: Run assess test and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_assess_generates_maturity_score_from_current_harness -q
```

Expected: pass.

## Task 4: Benchmark Schema Check

**Files:**
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/integration/test_benchmark_command.py`
- Modify: `docs/engineering/init-workflow.md`

- [x] **Step 1: Write failing benchmark assertion**

In benchmark integration, assert `"schema:maturity-evidence"` is present in check ids.

- [x] **Step 2: Run benchmark test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q
```

Expected: fail until benchmark validates the new schema.

- [x] **Step 3: Add benchmark schema validation**

Import `MaturityEvidencePack` and validate `.ai/maturity-evidence.yaml`.

- [x] **Step 4: Update engineering doc**

Add `.ai/maturity-evidence.yaml` to machine-consumed init assets and describe it as the deterministic evidence input for maturity review.

- [x] **Step 5: Run benchmark test and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q
```

Expected: pass.

## Task 5: Verification and Commit

**Files:**
- All modified files.

- [x] **Step 1: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py tests/unit/test_asset_writer_reports.py tests/integration/test_assess_improve_commands.py tests/integration/test_benchmark_command.py -q
```

Expected: pass.

- [x] **Step 2: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [x] **Step 3: Self-Harness Improvement Gate**

Check whether AGENTS, engineering docs, benchmark, or tests need additional updates. For this milestone, the expected gate result is that `init-workflow.md`, benchmark schema checks, asset writer tests, and integration tests cover the new contract.

- [x] **Step 4: Commit**

Run:

```bash
git add src/harness_builder_agent/schemas/maturity_evidence.py src/harness_builder_agent/tools/maturity_evidence.py src/harness_builder_agent/tools/asset_writers/reports.py src/harness_builder_agent/tools/assess_maturity.py src/harness_builder_agent/tools/benchmark.py src/harness_builder_agent/cli.py docs/engineering/init-workflow.md tests/unit/test_schema_contracts.py tests/unit/test_asset_writer_reports.py tests/integration/test_assess_improve_commands.py tests/integration/test_benchmark_command.py docs/superpowers/plans/2026-05-31-maturity-evidence-pack.md
git commit -m "feat: add maturity evidence pack"
```

Expected: commit succeeds after pre-commit fast regression.
