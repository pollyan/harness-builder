# LLM Workflow Routing Recommendation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation steps and superpowers:verification-before-completion before commit/push.

**Goal:** Add a review-only LLM workflow recommendation command that evaluates a task brief against the generated workflow routing policy.

**Architecture:** Add a schema and parser for recommendation output, a focused LLM prompt module, a writer/orchestrator that reads existing Harness config and maturity evidence, and a CLI command. The output lives under `.ai/review/` and does not execute workflows or generate `.ai/task-runs`.

**Tech Stack:** Python, Typer, Pydantic v2, YAML, pytest.

---

## Files

- Create: `src/harness_builder_agent/schemas/workflow_recommendation.py`
- Create: `src/harness_builder_agent/tools/llm_workflow_router.py`
- Create: `src/harness_builder_agent/tools/recommend_workflow.py`
- Create: `tests/unit/test_llm_workflow_router.py`
- Modify: `src/harness_builder_agent/cli.py`
- Modify: `docs/engineering/llm-contracts.md`
- Modify: `docs/engineering/architecture.md`
- Modify: `docs/superpowers/plans/2026-05-31-llm-workflow-routing-recommendation.md`

## Task 1: Schema and Parser

- [ ] **Step 1: Add failing unit tests**

Create `tests/unit/test_llm_workflow_router.py` with tests for:

- valid LLM recommendation response;
- invalid JSON;
- unknown selected workflow;
- unknown routing rule ID;
- prompt includes task brief, routing rules, and review-only boundary.

Use this test shape:

```python
def test_parse_workflow_recommendation_accepts_valid_response():
    report = parse_workflow_recommendation_response(
        json.dumps(
            {
                "task_id": "task-1",
                "task_brief": "Fix checkout permission bug.",
                "recommended_workflow": "bugfix",
                "matched_rule_ids": ["bugfix-intent"],
                "risk_level": "medium",
                "confidence": "high",
                "rationale": "Bugfix intent matches.",
                "required_guides": [".ai/guides/task-templates/bugfix.md"],
                "required_sensors": [".ai/sensors/verification.md"],
                "human_confirmation_required": False,
                "evidence_sources": [".ai/harness-config.yaml", ".ai/maturity-evidence.yaml"],
            }
        ),
        configured_workflows={"lightweight", "bugfix", "standard"},
        routing_rule_ids={"bugfix-intent", "low-risk-lightweight", "standard-escalation"},
    )

    assert report.recommended_workflow == "bugfix"
    assert report.review_status == "pending_harness_maintainer_review"
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_workflow_router.py -q
```

Expected: fail because module/schema do not exist.

- [ ] **Step 3: Add schema and parser**

Create `schemas/workflow_recommendation.py` with `WorkflowRecommendationReport`.

Create `tools/llm_workflow_router.py` with:

- `WORKFLOW_ROUTER_PROMPT_VERSION = "llm-workflow-router-v1"`
- `build_workflow_recommendation_messages(...)`
- `parse_workflow_recommendation_response(...)`
- `recommend_workflow_with_llm(...)`

Parser requirements:

- parse JSON only;
- validate Pydantic schema;
- reject unknown `recommended_workflow`;
- reject unknown `matched_rule_ids`;
- reject evidence sources not under `.ai/`.

- [ ] **Step 4: Run unit tests and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_workflow_router.py -q
```

## Task 2: Orchestrator and CLI

- [ ] **Step 1: Add failing integration test**

In `tests/integration/test_assess_improve_commands.py`, add `test_recommend_workflow_writes_review_only_artifacts`.

The test should:

- prepare a harness repo;
- monkeypatch `harness_builder_agent.tools.recommend_workflow.recommend_workflow_with_llm`;
- run `CliRunner().invoke(app, ["recommend-workflow", "--repo", str(repo), "--task", "Fix checkout permission bug.", "--task-id", "task-1"])`;
- assert YAML and Markdown files exist;
- validate YAML with `WorkflowRecommendationReport`;
- assert selected workflow is `bugfix`;
- assert `.ai/task-runs` does not exist.

- [ ] **Step 2: Run integration test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_recommend_workflow_writes_review_only_artifacts -q
```

Expected: fail because command does not exist.

- [ ] **Step 3: Add orchestrator and CLI command**

Create `tools/recommend_workflow.py`:

- read `harness-config.yaml` and `maturity-evidence.yaml`;
- call `recommend_workflow_with_llm`;
- write `.ai/review/workflow-routing-recommendation.yaml`;
- write `.ai/review/workflow-routing-recommendation.md`;
- return `.ai`.

Update `cli.py` with:

```python
@app.command("recommend-workflow")
def recommend_workflow_command(...):
```

Trace artifacts:

- `.ai/review/workflow-routing-recommendation.yaml`
- `.ai/review/workflow-routing-recommendation.md`

- [ ] **Step 4: Run integration test and confirm pass**

Run the same pytest command. Expected: pass.

## Task 3: Docs and Verification

- [ ] **Step 1: Update engineering docs**

In `docs/engineering/llm-contracts.md`, add workflow recommendation as a structured LLM output and state that failures must be explicit with no deterministic fallback.

In `docs/engineering/architecture.md`, add `recommend-workflow` to current core commands as review-only task routing recommendation, not runtime execution.

- [ ] **Step 2: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_workflow_router.py tests/integration/test_assess_improve_commands.py::test_recommend_workflow_writes_review_only_artifacts -q
```

- [ ] **Step 3: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

- [ ] **Step 4: Self-Harness Improvement Gate**

Record result here:

- Schema, parser, prompt, CLI integration, and docs cover the recommendation contract.
- No `.ai/task-runs` generation is introduced.
- Next candidate gap: benchmark check for recommendation artifacts if/when they become required, or runtime handoff contract refinement.

- [ ] **Step 5: Commit**

Commit message:

```bash
git commit -m "feat: recommend workflow from task brief"
```
