# Experience Source Aware LLM Prompts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make LLM maturity review and asset candidate prompts explicitly use `maturity_evidence.experience.sources`.

**Architecture:** Add prompt-contract guidance only. Existing schemas already carry the source details in `MaturityEvidencePack`, so implementation is limited to prompt strings, prompt tests, and LLM contract docs.

**Tech Stack:** Python, pytest, Pydantic schemas, DeepSeek-compatible chat message payloads.

---

### Task 1: Add Failing Prompt Tests

**Files:**
- Modify: `tests/unit/test_llm_maturity_reviewer.py`
- Modify: `tests/unit/test_llm_asset_candidate_generator.py`

- [ ] **Step 1: Add imports**

In both test files, import:

```python
from harness_builder_agent.schemas.experience_index import ExperienceSource
from harness_builder_agent.schemas.maturity_evidence import ExperienceEvidence
```

- [ ] **Step 2: Add maturity reviewer test**

Add:

```python
def test_build_maturity_review_messages_guides_experience_source_details():
    evidence = _evidence_pack()
    evidence.experience = ExperienceEvidence(
        has_experience_index=True,
        sources=[
            ExperienceSource(path=".ai/review/maturity-review.yaml", kind="maturity_review", item_count=1),
            ExperienceSource(path=".ai/review/asset-candidates.yaml", kind="asset_candidates", item_count=2),
            ExperienceSource(path=".ai/review/workflow-routing-recommendation.yaml", kind="workflow_recommendation", item_count=1),
        ],
    )

    messages = build_maturity_review_messages(_score(), evidence, _candidates())

    content = messages[-1]["content"]
    assert "maturity_evidence.experience.sources" in content
    assert "path, kind, and item_count" in content
    assert ".ai/review/asset-candidates.yaml" in content
    assert "review-only source index" in content
    assert "not applied Harness changes" in content
```

- [ ] **Step 3: Add asset candidate prompt test**

Add:

```python
def test_build_asset_candidate_messages_guides_experience_source_details():
    evidence = _evidence_pack()
    evidence.experience = ExperienceEvidence(
        has_experience_index=True,
        sources=[
            ExperienceSource(path=".ai/review/maturity-review.yaml", kind="maturity_review", item_count=1),
            ExperienceSource(path=".ai/review/asset-candidates.yaml", kind="asset_candidates", item_count=2),
            ExperienceSource(path=".ai/review/workflow-routing-recommendation.yaml", kind="workflow_recommendation", item_count=1),
        ],
    )

    messages = build_asset_candidate_messages(_score(), evidence, _improvement_candidates(), _maturity_review())

    content = messages[-1]["content"]
    assert "maturity_evidence.experience.sources" in content
    assert "path, kind, and item_count" in content
    assert ".ai/review/maturity-review.yaml" in content
    assert "review-only source index" in content
    assert "Do not invent missing source paths" in content
```

- [ ] **Step 4: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_maturity_reviewer.py::test_build_maturity_review_messages_guides_experience_source_details tests/unit/test_llm_asset_candidate_generator.py::test_build_asset_candidate_messages_guides_experience_source_details -q
```

Expected: FAIL because the prompt contract lacks source-aware guidance.

### Task 2: Implement Prompt Guidance

**Files:**
- Modify: `src/harness_builder_agent/tools/llm_maturity_reviewer.py`
- Modify: `src/harness_builder_agent/tools/llm_asset_candidate_generator.py`
- Modify: `docs/engineering/llm-contracts.md`

- [ ] **Step 1: Update maturity reviewer prompt**

Add to the schema contract:

```text
Use maturity_evidence.experience.sources as a review-only source index. Inspect each source path, kind, and item_count to identify available pending improvement, maturity review, asset candidate, workflow recommendation, or runtime evidence.
Prefer evidence_sources that cite paths present in maturity_evidence.experience.sources when those sources support the judgment.
Experience sources are not applied Harness changes; do not treat review-only source entries as formal Guides, Sensors, Workflow, or config updates.
```

- [ ] **Step 2: Update asset candidate prompt**

Add to the schema contract:

```text
Use maturity_evidence.experience.sources as a review-only source index. Inspect each source path, kind, and item_count to locate maturity review, asset candidate, workflow recommendation, pending improvement, or runtime evidence for draft candidates.
Ground candidate evidence_sources in paths that are present in maturity_evidence.experience.sources or other provided .ai evidence.
Do not invent missing source paths, and do not treat review-only source entries as applied Harness rules.
```

- [ ] **Step 3: Update LLM engineering docs**

Add one bullet explaining that maturity review and asset candidate prompts must explicitly consume `maturity_evidence.experience.sources` as review-only source index metadata.

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_maturity_reviewer.py tests/unit/test_llm_asset_candidate_generator.py -q
```

Expected: both prompt test files pass.

### Task 3: Verify And Commit

**Files:**
- Created spec and plan files.
- Modified prompt modules, prompt tests, and LLM contract docs.

- [ ] **Step 1: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: fast suite passes.

- [ ] **Step 2: Commit**

Run:

```bash
git add docs/engineering/llm-contracts.md docs/superpowers/specs/2026-05-31-experience-source-aware-llm-prompts-design.md docs/superpowers/plans/2026-05-31-experience-source-aware-llm-prompts.md src/harness_builder_agent/tools/llm_maturity_reviewer.py src/harness_builder_agent/tools/llm_asset_candidate_generator.py tests/unit/test_llm_maturity_reviewer.py tests/unit/test_llm_asset_candidate_generator.py
git commit -m "feat: guide llm prompts with experience sources"
```

- [ ] **Step 3: Run full regression and push**

Run:

```bash
scripts/test-full.sh
git push
scripts/check-ci.sh
```

Expected: local full suite passes before push; push succeeds; CI status is checked after push.
