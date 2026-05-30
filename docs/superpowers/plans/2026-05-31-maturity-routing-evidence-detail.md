# Maturity Routing Evidence Detail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation steps and superpowers:verification-before-completion before commit/push.

**Goal:** Add detailed workflow routing rules to `maturity-evidence.yaml` so LLM review and asset candidate generation can reason from structured routing evidence.

**Architecture:** Treat `harness-config.yaml` as the source of truth. Extend the Pydantic maturity evidence schema with a nested workflow routing rule summary, populate it from `HarnessConfig.workflow_routing`, and add benchmark consistency checks against the config. No runtime execution or LLM call is added.

**Tech Stack:** Python, Pydantic v2, YAML, pytest.

---

## Files

- Modify: `src/harness_builder_agent/schemas/maturity_evidence.py`
- Modify: `src/harness_builder_agent/tools/maturity_evidence.py`
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/unit/test_schema_contracts.py`
- Modify: `tests/unit/test_maturity_evidence.py`
- Modify: `tests/unit/test_llm_maturity_reviewer.py`
- Modify: `tests/integration/test_assess_improve_commands.py`
- Modify: `tests/integration/test_benchmark_command.py`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/superpowers/plans/2026-05-31-maturity-routing-evidence-detail.md`

## Task 1: Schema and Collection

- [ ] **Step 1: Write failing schema assertions**

In `tests/unit/test_schema_contracts.py`, update `test_maturity_evidence_pack_records_harness_inputs_for_review` so `harness_assets` includes:

```python
"workflow_routing_rules": [
    {
        "id": "standard-escalation",
        "selected_workflow": "standard",
        "task_type_hints": ["feature"],
        "triggers": ["high_risk_module", "security_or_permission"],
        "required_guides": [".ai/guides/architecture.md"],
        "required_sensors": [".ai/sensors/verification.md"],
        "human_confirmation_required": True,
        "rationale": "Escalate risky work.",
    }
],
```

and assert:

```python
assert pack.harness_assets.workflow_routing_rules[0].id == "standard-escalation"
assert "security_or_permission" in pack.harness_assets.workflow_routing_rules[0].triggers
```

- [ ] **Step 2: Write failing collector assertions**

In `tests/unit/test_maturity_evidence.py`, assert:

```python
standard_rule = next(rule for rule in pack.harness_assets.workflow_routing_rules if rule.id == "standard-escalation")
assert standard_rule.selected_workflow == "standard"
assert "cross_module_design" in standard_rule.triggers
assert standard_rule.human_confirmation_required is True
```

- [ ] **Step 3: Run targeted tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_maturity_evidence_pack_records_harness_inputs_for_review tests/unit/test_maturity_evidence.py::test_collect_maturity_evidence_uses_experience_index -q
```

Expected: fail because `WorkflowRoutingRuleEvidence` and `workflow_routing_rules` do not exist.

- [ ] **Step 4: Add schema and collector implementation**

In `schemas/maturity_evidence.py`, add:

```python
class WorkflowRoutingRuleEvidence(BaseModel):
    id: str
    selected_workflow: Literal["lightweight", "bugfix", "standard"]
    task_type_hints: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    required_guides: list[str] = Field(default_factory=list)
    required_sensors: list[str] = Field(default_factory=list)
    human_confirmation_required: bool = False
    rationale: str = ""
```

Add `workflow_routing_rules: list[WorkflowRoutingRuleEvidence] = Field(default_factory=list)` to `HarnessAssetEvidence`.

In `tools/maturity_evidence.py`, map each `config.workflow_routing.rules` item into `WorkflowRoutingRuleEvidence`.

- [ ] **Step 5: Run targeted tests and confirm pass**

Run the same pytest command. Expected: pass.

## Task 2: LLM Prompt Visibility and Integration Evidence

- [ ] **Step 1: Write failing LLM prompt assertion**

In `tests/unit/test_llm_maturity_reviewer.py`, update the fixture evidence pack to include routing details and assert the prompt content contains:

```python
assert "standard-escalation" in user_message
assert "security_or_permission" in user_message
```

- [ ] **Step 2: Write failing integration assertion**

In `tests/integration/test_assess_improve_commands.py`, assert generated `maturity-evidence.yaml` has the standard routing rule and trigger:

```python
rules = evidence_pack["harness_assets"]["workflow_routing_rules"]
standard_rule = next(rule for rule in rules if rule["id"] == "standard-escalation")
assert "security_or_permission" in standard_rule["triggers"]
```

- [ ] **Step 3: Run targeted tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_maturity_reviewer.py tests/integration/test_assess_improve_commands.py::test_assess_generates_maturity_score_from_current_harness -q
```

Expected: fail until collector emits detailed rules.

- [ ] **Step 4: Confirm pass after Task 1 implementation**

Run the same pytest command. Expected: pass.

## Task 3: Benchmark Consistency Check

- [ ] **Step 1: Write failing benchmark assertions**

In `tests/integration/test_benchmark_command.py`, assert generated report includes `content:maturity-routing-evidence`.

Add a test that removes `workflow_routing_rules` from `maturity-evidence.yaml` after a passing benchmark repo is prepared and then calls `_content_checks`; the new check must fail with `missing_routing_evidence_detail`.

- [ ] **Step 2: Run benchmark tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q
```

Expected: fail until benchmark checks detailed maturity routing evidence.

- [ ] **Step 3: Add benchmark check**

In `benchmark.py`, add `_maturity_routing_evidence_check(ai)` to `_content_checks`.

The check should:

- parse `HarnessConfig` and `MaturityEvidencePack`;
- compare config rule ids with evidence rule ids;
- require `standard-escalation` with `security_or_permission`;
- fail with `missing_routing_evidence_detail` when detail is absent.

- [ ] **Step 4: Run benchmark tests and confirm pass**

Run the same pytest command. Expected: pass.

## Task 4: Docs, Verification, Commit

- [ ] **Step 1: Update engineering docs**

Update `docs/engineering/init-workflow.md` to state that `maturity-evidence.yaml` includes detailed workflow routing evidence for LLM review and benchmark consistency checks.

- [ ] **Step 2: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py tests/unit/test_maturity_evidence.py tests/unit/test_llm_maturity_reviewer.py tests/integration/test_assess_improve_commands.py tests/integration/test_benchmark_command.py -q
```

- [ ] **Step 3: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

- [ ] **Step 4: Self-Harness Improvement Gate**

Record the result in this plan. Expected:

- Schema, collector, LLM prompt visibility, integration, benchmark, and docs cover detailed routing evidence.
- No `.ai/task-runs` generation is introduced.
- Next candidate gap: LLM-assisted routing recommendation or routing-aware asset candidate drafts.

- [ ] **Step 5: Commit**

Commit message:

```bash
git commit -m "feat: expose workflow routing in maturity evidence"
```
