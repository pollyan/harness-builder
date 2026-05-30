# Workflow Routing Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation steps and superpowers:verification-before-completion before commit/push.

**Goal:** Add a machine-readable workflow routing policy to `harness-config.yaml`, maturity evidence, and benchmark checks.

**Architecture:** Extend `HarnessConfig` with Pydantic routing rule models. Keep routing deterministic and config-owned. Benchmark and maturity evidence consume the config; no runtime execution or `.ai/task-runs` generation is introduced.

**Tech Stack:** Python, Pydantic v2, YAML, pytest.

---

## Files

- Modify: `src/harness_builder_agent/schemas/harness_config.py`
- Modify: `src/harness_builder_agent/schemas/maturity_evidence.py`
- Modify: `src/harness_builder_agent/tools/maturity_evidence.py`
- Modify: `src/harness_builder_agent/tools/maturity_model.py`
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/unit/test_schema_contracts.py`
- Modify: `tests/unit/test_maturity_evidence.py`
- Modify: `tests/integration/test_init_on_fixture_projects.py`
- Modify: `tests/integration/test_benchmark_command.py`
- Modify: `tests/integration/test_assess_improve_commands.py`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/engineering/architecture.md`
- Modify: `docs/superpowers/plans/2026-05-31-workflow-routing-policy.md`

## Task 1: Harness Config Routing Contract

- [ ] **Step 1: Write failing schema assertions**

In `tests/unit/test_schema_contracts.py`, extend `test_harness_config_has_lightweight_and_bugfix_workflows`:

```python
routing = config.workflow_routing
rule_ids = {rule.id for rule in routing.rules}
assert routing.default_workflow == "lightweight"
assert {"bugfix-intent", "low-risk-lightweight", "standard-escalation"}.issubset(rule_ids)
standard_rule = next(rule for rule in routing.rules if rule.id == "standard-escalation")
assert standard_rule.selected_workflow == "standard"
assert standard_rule.human_confirmation_required is True
assert "cross_module_design" in standard_rule.triggers
assert "security_or_permission" in standard_rule.triggers
assert "insufficient_sensor_coverage" in standard_rule.triggers
```

- [ ] **Step 2: Run schema test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_harness_config_has_lightweight_and_bugfix_workflows -q
```

Expected: fail because `workflow_routing` does not exist.

- [ ] **Step 3: Add Pydantic routing models and defaults**

Add `WorkflowRoutingRule` and `WorkflowRoutingPolicy` to `schemas/harness_config.py`, then add `workflow_routing` to `HarnessConfig`.

Default policy:

- `bugfix-intent` → `bugfix`
- `low-risk-lightweight` → `lightweight`
- `standard-escalation` → `standard`

Keep `RuntimeConfig.default_workflow = "lightweight"`.

- [ ] **Step 4: Run schema test and confirm pass**

Run the same pytest command. Expected: pass.

## Task 2: Init Serialization and Maturity Evidence

- [ ] **Step 1: Write failing init/evidence assertions**

In `tests/integration/test_init_on_fixture_projects.py`, assert generated config has routing and standard escalation.

In `tests/unit/test_maturity_evidence.py` and `tests/integration/test_assess_improve_commands.py`, assert:

```python
assert pack.harness_assets.workflow_routing_rule_count == 3
assert pack.harness_assets.has_standard_escalation_rule is True
```

- [ ] **Step 2: Run targeted tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_maturity_evidence.py tests/integration/test_init_on_fixture_projects.py tests/integration/test_assess_improve_commands.py::test_assess_generates_maturity_score_from_current_harness -q
```

Expected: fail until maturity evidence includes routing fields.

- [ ] **Step 3: Add maturity evidence fields and collection**

Extend `HarnessAssetEvidence` with:

```python
workflow_routing_rule_count: int = 0
has_standard_escalation_rule: bool = False
```

Populate these from `config.workflow_routing.rules`.

- [ ] **Step 4: Run targeted tests and confirm pass**

Run the same pytest command. Expected: pass.

## Task 3: Benchmark and Maturity Model Consumption

- [ ] **Step 1: Write failing benchmark assertions**

In `tests/integration/test_benchmark_command.py`, assert benchmark includes `content:workflow-routing-policy`, and add a test that removes the `standard-escalation` rule from `harness-config.yaml`; benchmark content check must fail.

- [ ] **Step 2: Run benchmark test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q
```

Expected: fail until benchmark checks routing.

- [ ] **Step 3: Add benchmark routing check and maturity wording**

In `benchmark.py`, add `_workflow_routing_policy_check`.

In `maturity_model.py`, use routing availability to distinguish workflow evidence and next-level requirements.

- [ ] **Step 4: Run benchmark test and confirm pass**

Run the same pytest command. Expected: pass.

## Task 4: Docs, Verification, Commit

- [ ] **Step 1: Update engineering docs**

Update architecture/init workflow docs to mention `workflow_routing` in `harness-config.yaml`.

- [ ] **Step 2: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py tests/unit/test_maturity_evidence.py tests/integration/test_init_on_fixture_projects.py tests/integration/test_benchmark_command.py tests/integration/test_assess_improve_commands.py -q
```

- [ ] **Step 3: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

- [ ] **Step 4: Self-Harness Improvement Gate**

Record result here before commit.

- [ ] **Step 5: Commit**

Commit message:

```bash
git commit -m "feat: add workflow routing policy"
```
