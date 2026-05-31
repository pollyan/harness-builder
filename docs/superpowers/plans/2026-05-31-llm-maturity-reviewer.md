# LLM Maturity Reviewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit `review-maturity` LLM review capability that evaluates maturity-driven improvement candidates and writes schema-validated review artifacts.

**Architecture:** Add a Pydantic schema for LLM review output, a focused LLM reviewer/parser module, and a thin orchestration tool used by a new CLI command. Keep default `improve` deterministic; LLM review is opt-in and fails explicitly when DeepSeek is unavailable.

**Tech Stack:** Python, Pydantic v2, PyYAML, Typer, pytest, existing DeepSeek client/config.

---

## Files

- Create: `src/harness_builder_agent/schemas/maturity_review.py`
- Create: `src/harness_builder_agent/tools/llm_maturity_reviewer.py`
- Create: `src/harness_builder_agent/tools/review_maturity.py`
- Modify: `src/harness_builder_agent/cli.py`
- Modify: `tests/unit/test_schema_contracts.py`
- Create: `tests/unit/test_llm_maturity_reviewer.py`
- Modify: `tests/integration/test_assess_improve_commands.py`
- Modify: `docs/superpowers/plans/2026-05-31-llm-maturity-reviewer.md`

## Task 1: Maturity Review Schema

**Files:**
- Modify: `tests/unit/test_schema_contracts.py`
- Create: `src/harness_builder_agent/schemas/maturity_review.py`

- [x] **Step 1: Write failing schema tests**

Add imports:

```python
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
```

Add tests:

```python
def test_maturity_review_report_records_candidate_judgment():
    report = MaturityReviewReport.model_validate(
        {
            "summary": "Candidates are directionally useful but need stronger acceptance checks.",
            "reviewer_model": "deepseek-test",
            "candidate_reviews": [
                {
                    "candidate_id": "maturity-next-step-guides",
                    "decision": "revise",
                    "rationale": "Guide update should be scoped to project-context first.",
                    "risks": ["May overgeneralize local rules."],
                    "suggested_acceptance_checks": ["Benchmark content:guides-quality passes."],
                    "evidence_sources": [".ai/maturity-evidence.yaml"],
                }
            ],
            "missing_candidates": ["Add runtime observability candidate."],
            "global_risks": ["No runtime task-runs are available."],
        }
    )

    assert report.schema_version == "1.0"
    assert report.candidate_reviews[0].decision == "revise"
    assert report.global_risks


def test_maturity_review_report_rejects_invalid_decision():
    with pytest.raises(ValidationError):
        MaturityReviewReport.model_validate(
            {
                "summary": "bad",
                "candidate_reviews": [
                    {
                        "candidate_id": "candidate-1",
                        "decision": "approve",
                        "rationale": "bad enum",
                    }
                ],
            }
        )
```

- [x] **Step 2: Run schema tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_maturity_review_report_records_candidate_judgment tests/unit/test_schema_contracts.py::test_maturity_review_report_rejects_invalid_decision -q
```

Expected: fail because `maturity_review.py` does not exist.

- [x] **Step 3: Implement schema**

Create `src/harness_builder_agent/schemas/maturity_review.py`:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MaturityCandidateReview(BaseModel):
    candidate_id: str
    decision: Literal["support", "revise", "defer"]
    rationale: str
    risks: list[str] = Field(default_factory=list)
    suggested_acceptance_checks: list[str] = Field(default_factory=list)
    evidence_sources: list[str] = Field(default_factory=list)


class MaturityReviewReport(BaseModel):
    schema_version: str = "1.0"
    summary: str
    reviewer_model: str | None = None
    candidate_reviews: list[MaturityCandidateReview] = Field(default_factory=list)
    missing_candidates: list[str] = Field(default_factory=list)
    global_risks: list[str] = Field(default_factory=list)
```

- [x] **Step 4: Run schema tests and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_maturity_review_report_records_candidate_judgment tests/unit/test_schema_contracts.py::test_maturity_review_report_rejects_invalid_decision -q
```

Expected: pass.

## Task 2: LLM Reviewer Parser and Validation

**Files:**
- Create: `tests/unit/test_llm_maturity_reviewer.py`
- Create: `src/harness_builder_agent/tools/llm_maturity_reviewer.py`

- [x] **Step 1: Write failing reviewer tests**

Create `tests/unit/test_llm_maturity_reviewer.py` with helpers that build minimal `MaturityReport`, `MaturityEvidencePack`, and `ImprovementCandidateReport`.

Add tests:

```python
def test_review_maturity_with_llm_returns_schema_valid_review():
    report = review_maturity_with_llm(
        _score(),
        _evidence_pack(),
        _candidates(),
        caller=lambda _messages: json.dumps(
            {
                "summary": "Review summary.",
                "reviewer_model": "deepseek-test",
                "candidate_reviews": [
                    {
                        "candidate_id": "candidate-1",
                        "decision": "support",
                        "rationale": "Candidate is aligned with maturity gap.",
                        "risks": [],
                        "suggested_acceptance_checks": ["Run benchmark."],
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                    }
                ],
                "missing_candidates": [],
                "global_risks": [],
            }
        ),
    )

    assert report.candidate_reviews[0].candidate_id == "candidate-1"
```

```python
def test_review_maturity_with_llm_rejects_unknown_candidate_id():
    with pytest.raises(ValueError, match="unknown candidate_id"):
        review_maturity_with_llm(
            _score(),
            _evidence_pack(),
            _candidates(),
            caller=lambda _messages: json.dumps(
                {
                    "summary": "bad",
                    "candidate_reviews": [
                        {"candidate_id": "missing", "decision": "support", "rationale": "bad"}
                    ],
                }
            ),
        )
```

```python
def test_parse_maturity_review_response_rejects_invalid_json():
    with pytest.raises(ValueError, match="must be valid JSON"):
        parse_maturity_review_response("not json", {"candidate-1"})
```

- [x] **Step 2: Run reviewer tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_maturity_reviewer.py -q
```

Expected: fail because module does not exist.

- [x] **Step 3: Implement reviewer module**

Create `src/harness_builder_agent/tools/llm_maturity_reviewer.py` with:

```python
REVIEW_PROMPT_VERSION = "llm-maturity-review-v1"

def review_maturity_with_llm(score, evidence_pack, candidates, caller=None, config=None) -> MaturityReviewReport:
    messages = build_maturity_review_messages(score, evidence_pack, candidates)
    content = caller(messages) if caller else call_deepseek(messages, config=config)
    if not content.strip():
        raise ValueError("DeepSeek maturity review response is empty")
    candidate_ids = {candidate.id for candidate in candidates.candidates}
    return parse_maturity_review_response(content, candidate_ids)
```

Add `build_maturity_review_messages(...)` with a strict JSON schema prompt and the three input payloads.

Add `parse_maturity_review_response(content, candidate_ids)`:

- extract fenced JSON using the same pattern as scan analyzer;
- parse JSON;
- validate `MaturityReviewReport`;
- reject any `candidate_review.candidate_id` not in `candidate_ids`.

- [x] **Step 4: Run reviewer tests and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_maturity_reviewer.py -q
```

Expected: pass.

## Task 3: CLI Orchestration and Artifacts

**Files:**
- Create: `src/harness_builder_agent/tools/review_maturity.py`
- Modify: `src/harness_builder_agent/cli.py`
- Modify: `tests/integration/test_assess_improve_commands.py`

- [x] **Step 1: Write failing CLI integration test**

Add `test_review_maturity_writes_llm_review_artifacts` to `tests/integration/test_assess_improve_commands.py`.

Use `_prepared_harness_repo`, run `assess`, run `improve`, monkeypatch the reviewer function:

```python
monkeypatch.setattr(
    "harness_builder_agent.tools.review_maturity.review_maturity_with_llm",
    lambda score, evidence_pack, candidates: MaturityReviewReport(
        summary="Candidates are aligned.",
        reviewer_model="deepseek-test",
        candidate_reviews=[
            {
                "candidate_id": candidates.candidates[0].id,
                "decision": "support",
                "rationale": "Candidate is grounded in maturity evidence.",
                "suggested_acceptance_checks": ["Run benchmark."],
                "evidence_sources": [".ai/maturity-evidence.yaml"],
            }
        ],
    ),
)
```

Run:

```python
result = CliRunner().invoke(app, ["review-maturity", "--repo", str(repo)])
```

Assert:

```python
assert result.exit_code == 0, result.output
review = yaml.safe_load((repo / ".ai" / "review" / "maturity-review.yaml").read_text(encoding="utf-8"))
markdown = (repo / ".ai" / "review" / "maturity-review.md").read_text(encoding="utf-8")
assert review["schema_version"] == "1.0"
assert review["candidate_reviews"][0]["decision"] == "support"
assert "# Maturity Review" in markdown
assert "## Candidate Reviews" in markdown
trace = _latest_trace(repo)
assert trace["command"] == "review-maturity"
```

- [x] **Step 2: Run CLI test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_review_maturity_writes_llm_review_artifacts -q
```

Expected: fail because command does not exist.

- [x] **Step 3: Implement orchestration tool**

Create `src/harness_builder_agent/tools/review_maturity.py`:

- ensure `.ai/maturity-score.yaml` and `.ai/maturity-evidence.yaml` exist by calling `assess_maturity(repo)`;
- ensure `.ai/improvement-candidates.yaml` exists by calling `generate_improvements(repo)`;
- load all three schema objects;
- call `review_maturity_with_llm(...)`;
- write `.ai/review/maturity-review.yaml`;
- write `.ai/review/maturity-review.md` with stable sections.

- [x] **Step 4: Add CLI command**

In `src/harness_builder_agent/cli.py`, add:

```python
@app.command("review-maturity")
def review_maturity_command(repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True)) -> None:
```

Create `GenerationTrace.start(repo, "review-maturity")`, call the orchestration tool, record both artifacts, and fail explicitly on exceptions.

- [x] **Step 5: Run CLI test and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_review_maturity_writes_llm_review_artifacts -q
```

Expected: pass.

## Task 4: Focused Verification and Commit

**Files:**
- All modified files.

- [x] **Step 1: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py tests/unit/test_llm_maturity_reviewer.py tests/integration/test_assess_improve_commands.py tests/integration/test_benchmark_command.py -q
```

Expected: pass.

- [x] **Step 2: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [x] **Step 3: Self-Harness Improvement Gate**

Check whether docs or benchmark need updates. Expected result: update `docs/engineering/llm-contracts.md` to mention LLM maturity review as a structured machine-consumed LLM output. Do not add default benchmark required files yet because the command is opt-in.

- [x] **Step 4: Commit**

Run:

```bash
git add src/harness_builder_agent/schemas/maturity_review.py src/harness_builder_agent/tools/llm_maturity_reviewer.py src/harness_builder_agent/tools/review_maturity.py src/harness_builder_agent/cli.py tests/unit/test_schema_contracts.py tests/unit/test_llm_maturity_reviewer.py tests/integration/test_assess_improve_commands.py docs/engineering/llm-contracts.md docs/superpowers/plans/2026-05-31-llm-maturity-reviewer.md
git commit -m "feat: add llm maturity reviewer"
```

Expected: commit succeeds after pre-commit fast regression.
