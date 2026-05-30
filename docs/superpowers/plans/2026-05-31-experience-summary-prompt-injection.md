# Experience Summary Prompt Injection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pass review-only Experience Summary findings into maturity review and asset candidate LLM prompts when the summary artifact exists.

**Architecture:** Add optional `ExperienceSummaryReport` parameters to the two LLM prompt builders and generator functions. Update orchestration modules to load `.ai/experience/experience-summary.yaml` only if present, then pass it through as optional context without changing output schemas or triggering extra LLM calls.

**Tech Stack:** Python, Pydantic v2, PyYAML, pytest.

---

## Files

- Modify: `src/harness_builder_agent/tools/llm_maturity_reviewer.py`
- Modify: `src/harness_builder_agent/tools/llm_asset_candidate_generator.py`
- Modify: `src/harness_builder_agent/tools/review_maturity.py`
- Modify: `src/harness_builder_agent/tools/generate_asset_candidates.py`
- Modify: `tests/unit/test_llm_maturity_reviewer.py`
- Modify: `tests/unit/test_llm_asset_candidate_generator.py`
- Modify: `tests/integration/test_assess_improve_commands.py`
- Modify: `docs/engineering/llm-contracts.md`
- Modify: `docs/superpowers/plans/2026-05-31-experience-summary-prompt-injection.md`

## Task 1: Prompt Builders Accept Optional Experience Summary

- [ ] **Step 1: Write failing maturity reviewer prompt test**

In `tests/unit/test_llm_maturity_reviewer.py`, import `ExperienceSummaryReport` and `build_maturity_review_messages`:

```python
from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
from harness_builder_agent.tools.llm_maturity_reviewer import build_maturity_review_messages
```

Add helper:

```python
def _experience_summary() -> ExperienceSummaryReport:
    return ExperienceSummaryReport(
        summary="Sensor coverage is the main repeated issue.",
        findings=[
            {
                "id": "sensor-coverage-gap",
                "kind": "sensor_feedback",
                "title": "Sensor coverage gap",
                "summary": "Pending improvements point to missing sensor coverage.",
                "evidence_sources": [".ai/experience/pending-improvements.md"],
                "confidence": "high",
            }
        ],
    )
```

Add test:

```python
def test_build_maturity_review_messages_includes_experience_summary_when_present():
    messages = build_maturity_review_messages(_score(), _evidence_pack(), _candidates(), experience_summary=_experience_summary())
    content = messages[-1]["content"]
    assert '"experience_summary"' in content
    assert "sensor-coverage-gap" in content
    assert "review-only Experience Summary findings" in content
```

- [ ] **Step 2: Write failing asset candidate prompt test**

In `tests/unit/test_llm_asset_candidate_generator.py`, import `ExperienceSummaryReport` and `build_asset_candidate_messages`:

```python
from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
from harness_builder_agent.tools.llm_asset_candidate_generator import build_asset_candidate_messages
```

Add helper:

```python
def _experience_summary() -> ExperienceSummaryReport:
    return ExperienceSummaryReport(
        summary="Workflow gaps are repeated.",
        findings=[
            {
                "id": "workflow-gap-routing",
                "kind": "workflow_gap",
                "title": "Workflow routing gap",
                "summary": "Experience findings point to missing routing rules.",
                "evidence_sources": [".ai/experience/experience-summary.yaml"],
                "confidence": "medium",
            }
        ],
    )
```

Add test:

```python
def test_build_asset_candidate_messages_includes_experience_summary_when_present():
    messages = build_asset_candidate_messages(
        _score(),
        _evidence_pack(),
        _improvement_candidates(),
        _maturity_review(),
        experience_summary=_experience_summary(),
    )
    content = messages[-1]["content"]
    assert '"experience_summary"' in content
    assert "workflow-gap-routing" in content
    assert "review-only Experience Summary findings" in content
```

- [ ] **Step 3: Run prompt tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_maturity_reviewer.py::test_build_maturity_review_messages_includes_experience_summary_when_present tests/unit/test_llm_asset_candidate_generator.py::test_build_asset_candidate_messages_includes_experience_summary_when_present -q
```

Expected: fail because prompt builders do not accept `experience_summary`.

- [ ] **Step 4: Implement optional prompt parameters**

In `src/harness_builder_agent/tools/llm_maturity_reviewer.py`:

1. Import `ExperienceSummaryReport`.
2. Add `experience_summary: ExperienceSummaryReport | None = None` to `review_maturity_with_llm` and `build_maturity_review_messages`.
3. Pass the parameter through.
4. Add to `schema_contract`:

```text
Use review-only Experience Summary findings when judging recurring gaps, sensor feedback, workflow gaps, and risk signals.
Do not treat Experience Summary findings as formal rules or applied changes.
```

5. Add `"experience_summary": experience_summary.model_dump(mode="json") if experience_summary else None` to payload.

In `src/harness_builder_agent/tools/llm_asset_candidate_generator.py`, make the same style of changes for `generate_asset_candidates_with_llm` and `build_asset_candidate_messages`.

- [ ] **Step 5: Run prompt tests and confirm pass**

Run the same pytest command. Expected: pass.

## Task 2: Orchestration Loads Existing Summary

- [ ] **Step 1: Write failing integration assertions**

In `tests/integration/test_assess_improve_commands.py`, extend `test_review_maturity_writes_llm_review_artifacts`:

1. Write a summary file before monkeypatch:

```python
(repo / ".ai" / "experience" / "experience-summary.yaml").write_text(
    yaml.safe_dump(
        {
            "summary": "Sensor coverage is the repeated signal.",
            "findings": [
                {
                    "id": "sensor-coverage-gap",
                    "kind": "sensor_feedback",
                    "title": "Sensor coverage gap",
                    "summary": "Pending improvements point to missing sensor coverage.",
                    "evidence_sources": [".ai/experience/pending-improvements.md"],
                }
            ],
        },
        sort_keys=False,
        allow_unicode=True,
    ),
    encoding="utf-8",
)
```

2. Change fake review signature:

```python
def fake_review(score, evidence_pack, candidates, experience_summary=None):
    assert experience_summary is not None
    assert experience_summary.findings[0].id == "sensor-coverage-gap"
```

In `test_generate_asset_candidates_writes_review_only_drafts`, write a summary file before monkeypatching asset candidates and change fake asset generator signature:

```python
def fake_asset_candidates(score, evidence_pack, improvement_candidates, maturity_review, experience_summary=None):
    assert experience_summary is not None
    assert experience_summary.findings[0].kind == "workflow_gap"
```

- [ ] **Step 2: Run integration tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_review_maturity_writes_llm_review_artifacts tests/integration/test_assess_improve_commands.py::test_generate_asset_candidates_writes_review_only_drafts -q
```

Expected: fail because orchestration does not load or pass `experience_summary`.

- [ ] **Step 3: Implement summary loading helper in both orchestrators**

In `src/harness_builder_agent/tools/review_maturity.py`:

1. Import `ExperienceSummaryReport`.
2. Add helper:

```python
def _load_experience_summary(ai: Path) -> ExperienceSummaryReport | None:
    path = ai / "experience" / "experience-summary.yaml"
    if not path.exists():
        return None
    return ExperienceSummaryReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
```

3. Call:

```python
experience_summary = _load_experience_summary(ai)
review = review_maturity_with_llm(score, evidence_pack, candidates, experience_summary=experience_summary)
```

In `src/harness_builder_agent/tools/generate_asset_candidates.py`, add the same helper and call:

```python
experience_summary = _load_experience_summary(ai)
report = generate_asset_candidates_with_llm(score, evidence_pack, improvement_candidates, maturity_review, experience_summary=experience_summary)
```

- [ ] **Step 4: Run integration tests and confirm pass**

Run the same pytest command. Expected: pass.

## Task 3: Compatibility Without Summary

- [ ] **Step 1: Add unit assertions that summary is optional**

In `tests/unit/test_llm_maturity_reviewer.py`, add:

```python
def test_build_maturity_review_messages_uses_null_experience_summary_when_absent():
    messages = build_maturity_review_messages(_score(), _evidence_pack(), _candidates())
    assert '"experience_summary": null' in messages[-1]["content"]
```

In `tests/unit/test_llm_asset_candidate_generator.py`, add:

```python
def test_build_asset_candidate_messages_uses_null_experience_summary_when_absent():
    messages = build_asset_candidate_messages(_score(), _evidence_pack(), _improvement_candidates(), _maturity_review())
    assert '"experience_summary": null' in messages[-1]["content"]
```

- [ ] **Step 2: Run compatibility tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_maturity_reviewer.py tests/unit/test_llm_asset_candidate_generator.py -q
```

Expected: pass.

## Task 4: Docs, Verification, Commit

- [ ] **Step 1: Update LLM contract docs**

In `docs/engineering/llm-contracts.md`, add that maturity review and asset candidate prompts should include optional `experience_summary` when `.ai/experience/experience-summary.yaml` exists, and must treat it as review-only semantic context.

- [ ] **Step 2: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_maturity_reviewer.py tests/unit/test_llm_asset_candidate_generator.py tests/integration/test_assess_improve_commands.py -q
```

Expected: pass.

- [ ] **Step 3: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [ ] **Step 4: Self-Harness Improvement Gate**

Record the gate result in this plan. Expected:

- Prompt tests cover both present and absent Experience Summary.
- Integration tests prove orchestration passes existing summaries.
- No output schemas or formal Harness assets were changed.
- No benchmark update is needed because this is optional prompt context.
- Next candidate gap: Workflow Toolkit Evolution or Experience Summary freshness metadata.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/harness_builder_agent/tools/llm_maturity_reviewer.py src/harness_builder_agent/tools/llm_asset_candidate_generator.py src/harness_builder_agent/tools/review_maturity.py src/harness_builder_agent/tools/generate_asset_candidates.py tests/unit/test_llm_maturity_reviewer.py tests/unit/test_llm_asset_candidate_generator.py tests/integration/test_assess_improve_commands.py docs/engineering/llm-contracts.md docs/superpowers/specs/2026-05-31-experience-summary-prompt-injection-design.md docs/superpowers/plans/2026-05-31-experience-summary-prompt-injection.md
git commit -m "feat: inject experience summary into llm prompts"
```

Expected: commit succeeds after pre-commit fast regression.
