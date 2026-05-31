# Human Confirmation Machine Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Pydantic schemas for `.ai/context-inputs.yaml` and `.ai/questionnaire.yaml`, then use them in generation and benchmark validation.

**Architecture:** Introduce a focused schema module for human confirmation machine contracts. Keep existing dict return shapes for low-risk compatibility, but validate at creation, writer, and benchmark boundaries.

**Tech Stack:** Python, Pydantic, pytest, YAML benchmark artifacts.

---

### Task 1: Add Failing Schema And Benchmark Tests

**Files:**
- Modify: `tests/unit/test_schema_contracts.py`
- Modify: `tests/unit/test_human_confirmation.py`
- Modify: `tests/integration/test_benchmark_command.py`

- [ ] **Step 1: Add schema contract tests**

In `tests/unit/test_schema_contracts.py`, import:

```python
from harness_builder_agent.schemas.human_confirmation import ContextInputs, Questionnaire
```

Add:

```python
def test_context_inputs_reject_negative_size():
    with pytest.raises(ValidationError):
        ContextInputs.model_validate(
            {
                "schema_version": "1.0",
                "contexts": [
                    {"path": "/repo/team.md", "size_bytes": -1, "summary": "team", "truncated": False}
                ],
            }
        )


def test_questionnaire_rejects_unknown_interaction_type():
    with pytest.raises(ValidationError):
        Questionnaire.model_validate(
            {
                "schema_version": "1.0",
                "questions": [
                    {
                        "interaction_type": "unknown",
                        "interaction_id": "confirm:unknown",
                        "question": "Confirm?",
                        "options": ["yes"],
                        "confidence": "medium",
                        "reason": "Needs confirmation.",
                    }
                ],
            }
        )
```

- [ ] **Step 2: Add generator validation assertions**

In `tests/unit/test_human_confirmation.py`, import:

```python
from harness_builder_agent.schemas.human_confirmation import ContextInputs, Questionnaire
```

Add assertions:

```python
ContextInputs.model_validate(payload)
Questionnaire.model_validate(questionnaire)
```

to the existing read/build tests.

- [ ] **Step 3: Add benchmark check id and invalid questionnaire test**

In `tests/integration/test_benchmark_command.py`, add to the happy-path check list:

```python
assert "schema:context-inputs" in check_ids
```

Add:

```python
def test_benchmark_fails_invalid_questionnaire_schema(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    path = ai / "questionnaire.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["questions"][0]["interaction_type"] = "unknown"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    checks = _human_confirmation_checks(ai)

    questionnaire = next(check for check in checks if check["id"] == "schema:questionnaire")
    assert questionnaire["passed"] is False
```

Also import `_human_confirmation_checks` from `harness_builder_agent.tools.benchmark`.

- [ ] **Step 4: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_context_inputs_reject_negative_size tests/unit/test_schema_contracts.py::test_questionnaire_rejects_unknown_interaction_type tests/unit/test_human_confirmation.py tests/integration/test_benchmark_command.py::test_benchmark_generates_report_for_java_fixture tests/integration/test_benchmark_command.py::test_benchmark_fails_invalid_questionnaire_schema -q
```

Expected: FAIL because `schemas.human_confirmation` does not exist and benchmark has no `schema:context-inputs` check.

### Task 2: Implement Schemas And Generation Validation

**Files:**
- Create: `src/harness_builder_agent/schemas/human_confirmation.py`
- Modify: `src/harness_builder_agent/tools/human_confirmation.py`
- Modify: `src/harness_builder_agent/tools/asset_writers/human_confirmation.py`

- [ ] **Step 1: Add schema module**

Create:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from harness_builder_agent.schemas.common import Confidence


class ContextInput(BaseModel):
    path: str
    size_bytes: int = Field(ge=0)
    summary: str
    truncated: bool


class ContextInputs(BaseModel):
    schema_version: str = "1.0"
    contexts: list[ContextInput] = Field(default_factory=list)


class QuestionnaireQuestion(BaseModel):
    interaction_type: Literal[
        "context_confirmation",
        "candidate_asset_confirmation",
        "sensor_gate_confirmation",
        "scan_warning_confirmation",
    ]
    interaction_id: str
    question: str
    options: list[str] = Field(min_length=1)
    confidence: Confidence
    reason: str


class Questionnaire(BaseModel):
    schema_version: str = "1.0"
    questions: list[QuestionnaireQuestion] = Field(min_length=1)
```

- [ ] **Step 2: Validate at builder boundary**

In `tools/human_confirmation.py`, import schemas and return validated dumps:

```python
from harness_builder_agent.schemas.human_confirmation import ContextInputs, Questionnaire
```

Use:

```python
return ContextInputs(contexts=contexts).model_dump(mode="json")
return Questionnaire(questions=questions).model_dump(mode="json")
```

- [ ] **Step 3: Validate at writer boundary**

In `asset_writers/human_confirmation.py`, validate before writing:

```python
context_payload = ContextInputs.model_validate(context_inputs).model_dump(mode="json")
questionnaire_payload = Questionnaire.model_validate(questionnaire).model_dump(mode="json")
```

Write and render with the validated payloads.

- [ ] **Step 4: Run generator tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_context_inputs_reject_negative_size tests/unit/test_schema_contracts.py::test_questionnaire_rejects_unknown_interaction_type tests/unit/test_human_confirmation.py tests/unit/test_asset_writer_human_confirmation.py -q
```

Expected: schema and writer tests pass.

### Task 3: Wire Benchmark Schema Validation

**Files:**
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `docs/engineering/init-workflow.md`

- [ ] **Step 1: Import schemas**

Add:

```python
from harness_builder_agent.schemas.human_confirmation import ContextInputs, Questionnaire
```

- [ ] **Step 2: Replace ad hoc questionnaire schema check**

In `_human_confirmation_checks`, parse `context-inputs.yaml` and `questionnaire.yaml` with Pydantic. Return `schema:context-inputs` and `schema:questionnaire` checks.

Keep `content:human-confirmation` based on required interaction ids and Markdown heading.

- [ ] **Step 3: Update engineering docs**

In `docs/engineering/init-workflow.md`, add that `context-inputs.yaml` and `questionnaire.yaml` are validated by `ContextInputs` and `Questionnaire`.

- [ ] **Step 4: Run benchmark tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py::test_benchmark_generates_report_for_java_fixture tests/integration/test_benchmark_command.py::test_benchmark_fails_invalid_questionnaire_schema -q
```

Expected: benchmark tests pass.

### Task 4: Verify And Commit

**Files:**
- Create: `src/harness_builder_agent/schemas/human_confirmation.py`
- Create: `docs/superpowers/specs/2026-05-31-human-confirmation-machine-contracts-design.md`
- Create: `docs/superpowers/plans/2026-05-31-human-confirmation-machine-contracts.md`
- Modify: `src/harness_builder_agent/tools/human_confirmation.py`
- Modify: `src/harness_builder_agent/tools/asset_writers/human_confirmation.py`
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/unit/test_schema_contracts.py`
- Modify: `tests/unit/test_human_confirmation.py`
- Modify: `tests/integration/test_benchmark_command.py`
- Modify: `docs/engineering/init-workflow.md`

- [ ] **Step 1: Run focused suite**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py tests/unit/test_human_confirmation.py tests/unit/test_asset_writer_human_confirmation.py tests/integration/test_benchmark_command.py tests/integration/test_init_on_fixture_projects.py -q
```

Expected: focused schema/init/benchmark suite passes.

- [ ] **Step 2: Run fast regression before commit**

Run:

```bash
scripts/test-fast.sh
```

Expected: fast suite passes.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/engineering/init-workflow.md docs/superpowers/specs/2026-05-31-human-confirmation-machine-contracts-design.md docs/superpowers/plans/2026-05-31-human-confirmation-machine-contracts.md src/harness_builder_agent/schemas/human_confirmation.py src/harness_builder_agent/tools/human_confirmation.py src/harness_builder_agent/tools/asset_writers/human_confirmation.py src/harness_builder_agent/tools/benchmark.py tests/unit/test_schema_contracts.py tests/unit/test_human_confirmation.py tests/integration/test_benchmark_command.py
git commit -m "feat: validate human confirmation contracts"
```

- [ ] **Step 4: Run full regression and push**

Run:

```bash
scripts/test-full.sh
git push
scripts/check-ci.sh
```

Expected: local full suite passes before push, push succeeds, and CI status is checked after push.
