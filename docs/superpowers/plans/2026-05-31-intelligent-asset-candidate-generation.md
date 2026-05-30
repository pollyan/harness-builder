# Intelligent Asset Candidate Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit LLM-powered command that converts maturity review into review-only Guide/Sensor/Workflow draft asset candidates.

**Architecture:** Add a schema for asset candidates, a focused LLM parser/generator module, and a CLI orchestration command. The command writes only `.ai/review/*` candidate files and never overwrites formal Harness assets.

**Tech Stack:** Python, Pydantic v2, PyYAML, Typer, pytest, existing DeepSeek client/config.

---

## Files

- Create: `src/harness_builder_agent/schemas/asset_candidate.py`
- Create: `src/harness_builder_agent/tools/llm_asset_candidate_generator.py`
- Create: `src/harness_builder_agent/tools/generate_asset_candidates.py`
- Modify: `src/harness_builder_agent/cli.py`
- Modify: `tests/unit/test_schema_contracts.py`
- Create: `tests/unit/test_llm_asset_candidate_generator.py`
- Modify: `tests/integration/test_assess_improve_commands.py`
- Modify: `docs/engineering/llm-contracts.md`
- Modify: `docs/superpowers/plans/2026-05-31-intelligent-asset-candidate-generation.md`

## Task 1: Asset Candidate Schema

**Files:**
- Modify: `tests/unit/test_schema_contracts.py`
- Create: `src/harness_builder_agent/schemas/asset_candidate.py`

- [ ] **Step 1: Write failing schema tests**

Add import:

```python
from harness_builder_agent.schemas.asset_candidate import AssetCandidateReport
```

Add tests:

```python
def test_asset_candidate_report_records_review_only_drafts():
    report = AssetCandidateReport.model_validate(
        {
            "candidates": [
                {
                    "id": "guide-project-context-scope",
                    "kind": "guide",
                    "source_candidate_id": "candidate-1",
                    "source_review_decision": "revise",
                    "suggested_path": ".ai/guides/project-context.md",
                    "title": "Scope project context guide",
                    "rationale": "The guide needs a more explicit task loading scope.",
                    "draft_content": "## Candidate Addition\n\nAdd task loading scope.",
                    "evidence_sources": [".ai/maturity-evidence.yaml"],
                    "acceptance_checks": ["Benchmark content:guides-quality passes."],
                    "risk_level": "medium",
                    "review_status": "pending_harness_maintainer_review",
                }
            ]
        }
    )

    assert report.schema_version == "1.0"
    assert report.candidates[0].kind == "guide"
    assert report.candidates[0].review_status == "pending_harness_maintainer_review"
```

```python
def test_asset_candidate_report_rejects_invalid_kind():
    with pytest.raises(ValidationError):
        AssetCandidateReport.model_validate(
            {
                "candidates": [
                    {
                        "id": "bad",
                        "kind": "unknown",
                        "source_review_decision": "support",
                        "suggested_path": ".ai/guides/project-context.md",
                        "title": "Bad",
                        "rationale": "Bad kind.",
                        "draft_content": "content",
                    }
                ]
            }
        )
```

- [ ] **Step 2: Run schema tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_asset_candidate_report_records_review_only_drafts tests/unit/test_schema_contracts.py::test_asset_candidate_report_rejects_invalid_kind -q
```

Expected: fail because `asset_candidate.py` does not exist.

- [ ] **Step 3: Implement schema**

Create `src/harness_builder_agent/schemas/asset_candidate.py`:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AssetCandidateDraft(BaseModel):
    id: str
    kind: Literal["guide", "sensor", "workflow_policy"]
    source_candidate_id: str | None = None
    source_review_decision: Literal["support", "revise", "defer", "missing"]
    suggested_path: str
    title: str
    rationale: str
    draft_content: str
    evidence_sources: list[str] = Field(default_factory=list)
    acceptance_checks: list[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"] = "medium"
    review_status: Literal["pending_harness_maintainer_review"] = "pending_harness_maintainer_review"


class AssetCandidateReport(BaseModel):
    schema_version: str = "1.0"
    source: str = "llm_maturity_review"
    candidates: list[AssetCandidateDraft] = Field(default_factory=list)
```

- [ ] **Step 4: Run schema tests and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_asset_candidate_report_records_review_only_drafts tests/unit/test_schema_contracts.py::test_asset_candidate_report_rejects_invalid_kind -q
```

Expected: pass.

## Task 2: LLM Asset Candidate Parser

**Files:**
- Create: `tests/unit/test_llm_asset_candidate_generator.py`
- Create: `src/harness_builder_agent/tools/llm_asset_candidate_generator.py`

- [ ] **Step 1: Write failing parser tests**

Create tests with minimal `MaturityReport`, `MaturityEvidencePack`, `ImprovementCandidateReport`, and `MaturityReviewReport`.

Test success:

```python
def test_generate_asset_candidates_with_llm_returns_schema_valid_candidates():
    report = generate_asset_candidates_with_llm(
        _score(),
        _evidence_pack(),
        _improvement_candidates(),
        _maturity_review(),
        caller=lambda _messages: json.dumps(
            {
                "candidates": [
                    {
                        "id": "guide-project-context-scope",
                        "kind": "guide",
                        "source_candidate_id": "candidate-1",
                        "source_review_decision": "support",
                        "suggested_path": ".ai/guides/project-context.md",
                        "title": "Scope project context guide",
                        "rationale": "Grounded in review.",
                        "draft_content": "## Candidate Addition\n\nAdd scope.",
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                        "acceptance_checks": ["Benchmark content:guides-quality passes."],
                        "risk_level": "medium",
                        "review_status": "pending_harness_maintainer_review",
                    }
                ]
            }
        ),
    )

    assert report.candidates[0].source_candidate_id == "candidate-1"
```

Test unknown source:

```python
def test_generate_asset_candidates_rejects_unknown_source_candidate_id():
    with pytest.raises(ValueError, match="unknown source_candidate_id"):
        parse_asset_candidate_response(
            json.dumps(
                {
                    "candidates": [
                        {
                            "id": "bad",
                            "kind": "guide",
                            "source_candidate_id": "missing",
                            "source_review_decision": "support",
                            "suggested_path": ".ai/guides/project-context.md",
                            "title": "Bad",
                            "rationale": "Bad source.",
                            "draft_content": "content",
                        }
                    ]
                }
            ),
            {"candidate-1"},
        )
```

Test non `.ai/` path:

```python
def test_generate_asset_candidates_rejects_non_ai_path():
    with pytest.raises(ValueError, match="suggested_path must be under .ai/"):
        parse_asset_candidate_response(
            json.dumps(
                {
                    "candidates": [
                        {
                            "id": "bad",
                            "kind": "guide",
                            "source_candidate_id": "candidate-1",
                            "source_review_decision": "support",
                            "suggested_path": "README.md",
                            "title": "Bad",
                            "rationale": "Bad path.",
                            "draft_content": "content",
                        }
                    ]
                }
            ),
            {"candidate-1"},
        )
```

- [ ] **Step 2: Run parser tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_asset_candidate_generator.py -q
```

Expected: fail because module does not exist.

- [ ] **Step 3: Implement generator module**

Create `src/harness_builder_agent/tools/llm_asset_candidate_generator.py`:

- `ASSET_CANDIDATE_PROMPT_VERSION = "llm-asset-candidate-v1"`.
- `generate_asset_candidates_with_llm(score, evidence_pack, improvement_candidates, maturity_review, caller=None, config=None)`.
- `build_asset_candidate_messages(...)`.
- `parse_asset_candidate_response(content, candidate_ids)`.

Parser rules:

- JSON only, fenced JSON accepted.
- Validate `AssetCandidateReport`.
- Reject unknown `source_candidate_id` unless `source_review_decision == "missing"`.
- Reject `suggested_path` values not starting `.ai/`.

- [ ] **Step 4: Run parser tests and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_asset_candidate_generator.py -q
```

Expected: pass.

## Task 3: CLI Orchestration and Review Artifacts

**Files:**
- Create: `src/harness_builder_agent/tools/generate_asset_candidates.py`
- Modify: `src/harness_builder_agent/cli.py`
- Modify: `tests/integration/test_assess_improve_commands.py`

- [ ] **Step 1: Write failing CLI integration test**

Add `test_generate_asset_candidates_writes_review_only_drafts`.

Use `_prepared_harness_repo`, then run:

```python
runner.invoke(app, ["assess", "--repo", str(repo)])
runner.invoke(app, ["improve", "--repo", str(repo)])
```

Monkeypatch `review_maturity_with_llm` so `review-maturity` can produce a review, then run `review-maturity`.

Monkeypatch:

```python
monkeypatch.setattr(
    "harness_builder_agent.tools.generate_asset_candidates.generate_asset_candidates_with_llm",
    lambda score, evidence_pack, improvement_candidates, maturity_review: AssetCandidateReport(
        candidates=[
            {
                "id": "guide-project-context-scope",
                "kind": "guide",
                "source_candidate_id": improvement_candidates.candidates[0].id,
                "source_review_decision": "support",
                "suggested_path": ".ai/guides/project-context.md",
                "title": "Scope project context guide",
                "rationale": "Candidate is grounded in maturity review.",
                "draft_content": "## Candidate Addition\n\nAdd task loading scope.",
                "evidence_sources": [".ai/maturity-evidence.yaml"],
                "acceptance_checks": ["Benchmark content:guides-quality passes."],
                "risk_level": "medium",
            }
        ]
    ),
)
```

Run:

```python
result = runner.invoke(app, ["generate-asset-candidates", "--repo", str(repo)])
```

Assert:

```python
assert result.exit_code == 0, result.output
asset_report = yaml.safe_load((repo / ".ai" / "review" / "asset-candidates.yaml").read_text(encoding="utf-8"))
guide_md = (repo / ".ai" / "review" / "asset-candidate-guides.md").read_text(encoding="utf-8")
assert asset_report["schema_version"] == "1.0"
assert asset_report["candidates"][0]["review_status"] == "pending_harness_maintainer_review"
assert "# Asset Candidate Guides" in guide_md
assert "Scope project context guide" in guide_md
assert (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
trace = _latest_trace(repo)
assert trace["command"] == "generate-asset-candidates"
```

- [ ] **Step 2: Run CLI test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_generate_asset_candidates_writes_review_only_drafts -q
```

Expected: fail because command does not exist.

- [ ] **Step 3: Implement orchestration tool**

Create `src/harness_builder_agent/tools/generate_asset_candidates.py`:

- ensure maturity score/evidence exists via `assess_maturity`;
- ensure improvement candidates exists via `generate_improvements`;
- ensure maturity review exists via `review_maturity`;
- load all four schema objects;
- call `generate_asset_candidates_with_llm`;
- write YAML and three grouped Markdown files.

Markdown sections:

- guide file: `# Asset Candidate Guides`
- sensor file: `# Asset Candidate Sensors`
- workflow file: `# Asset Candidate Workflows`

- [ ] **Step 4: Add CLI command**

Add `generate-asset-candidates` command in `cli.py` with `GenerationTrace.start(repo, "generate-asset-candidates")`, artifact records for all four files, and explicit failure trace.

- [ ] **Step 5: Run CLI test and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_generate_asset_candidates_writes_review_only_drafts -q
```

Expected: pass.

## Task 4: Verification, Docs, Commit

**Files:**
- All modified files.

- [ ] **Step 1: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py tests/unit/test_llm_asset_candidate_generator.py tests/integration/test_assess_improve_commands.py tests/integration/test_benchmark_command.py -q
```

Expected: pass.

- [ ] **Step 2: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [ ] **Step 3: Self-Harness Improvement Gate**

Update `docs/engineering/llm-contracts.md` to include asset candidate generation as structured LLM output. Do not add these opt-in review artifacts to benchmark required files yet.

- [ ] **Step 4: Commit**

Run:

```bash
git add src/harness_builder_agent/schemas/asset_candidate.py src/harness_builder_agent/tools/llm_asset_candidate_generator.py src/harness_builder_agent/tools/generate_asset_candidates.py src/harness_builder_agent/cli.py tests/unit/test_schema_contracts.py tests/unit/test_llm_asset_candidate_generator.py tests/integration/test_assess_improve_commands.py docs/engineering/llm-contracts.md docs/superpowers/plans/2026-05-31-intelligent-asset-candidate-generation.md
git commit -m "feat: generate intelligent asset candidates"
```

Expected: commit succeeds after pre-commit fast regression.
