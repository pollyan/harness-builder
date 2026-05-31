# Workflow Policy Candidate Apply Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow reviewed `workflow_policy` asset candidates to apply a schema-valid routing rule patch to `.ai/harness-config.yaml`.

**Architecture:** Add a small Pydantic patch schema embedded as `AssetCandidateDraft.workflow_policy_patch`, extend `candidate_governance.review_candidate` to dispatch workflow policy patches, validate against `HarnessConfig` and formal `.ai/` assets, then refresh governance, Experience index, and maturity evidence. Keep LLM candidates review-only and reject free-text workflow policy drafts.

**Tech Stack:** Python, Typer, Pydantic, PyYAML, pytest.

---

### Task 1: Patch Schema

**Files:**
- Create: `src/harness_builder_agent/schemas/workflow_policy_patch.py`
- Modify: `tests/unit/test_schema_contracts.py`

- [x] Write failing schema tests for valid `upsert_routing_rule` and invalid operation/target.
- [x] Implement `WorkflowPolicyPatch` using existing `WorkflowRoutingRule`.
- [x] Run targeted schema tests.

### Task 2: Workflow Policy Apply Tool

**Files:**
- Modify: `src/harness_builder_agent/tools/candidate_governance.py`
- Modify: `tests/unit/test_candidate_governance.py`

- [x] Write failing tests for applying a workflow policy candidate and rejecting unsafe patches.
- [x] Require `candidate.workflow_policy_patch` and reject free-text-only workflow candidates.
- [x] Upsert routing rule by id in `HarnessConfig`.
- [x] Validate selected workflow and required guide/sensor references.
- [x] Refresh governance log, Experience index, maturity score, and maturity evidence.

### Task 3: CLI And Benchmark Coverage

**Files:**
- Modify: `tests/integration/test_assess_improve_commands.py`
- Modify: `tests/integration/test_benchmark_command.py`
- Modify: `src/harness_builder_agent/tools/benchmark.py`

- [x] Add CLI integration test for workflow policy applied.
- [x] Assert benchmark workflow routing, maturity routing evidence, and candidate governance checks pass after application.
- [x] Add benchmark failure coverage if governance applied path, source candidate references, or applied workflow patch drift.
- [x] Make benchmark preserve existing `.ai/` assets when validating an initialized Harness.

### Task 4: Prompt And Docs

**Files:**
- Modify: `src/harness_builder_agent/prompts/llm_asset_candidate_v2.md`
- Modify: `tests/unit/test_llm_asset_candidate_generator.py`
- Modify: `README.md`
- Modify: `docs/engineering/architecture.md`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/engineering/sensor-and-gate-rules.md`
- Modify: `docs/evolution-log.md`
- Modify: `docs/todos/README.md`
- Move or archive: `docs/todos/workflow-policy-candidate-apply.md`

- [x] Require workflow policy candidates to provide structured `workflow_policy_patch`; keep `draft_content` as human explanation only.
- [x] Document the applied boundary.
- [x] Archive the completed todo.

### Task 5: Verification And Commit

- [x] Run targeted tests.
- [x] Run `scripts/test-fast.sh`.
- [x] Commit locally.
