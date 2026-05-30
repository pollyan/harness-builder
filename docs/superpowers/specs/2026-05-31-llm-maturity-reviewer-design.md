# LLM Maturity Reviewer Design

## Context

This is the fourth autonomous milestone in the strategy-guided loop.

North Star reference:

- `docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`
- `4.1 Core Harness 与 Improvement System`
- `6.5 Experience & Self-Improve：经验沉淀与自我演进`
- `6.6 Maturity & Evolution：成熟度评估与演进路径`

Previous milestones created the deterministic foundation:

- `Maturity Model v2`
- `Maturity Evidence Pack`
- `Maturity-driven Improve`

## Current State Gap Analysis

Current `improve` now generates candidates from maturity next steps, active caps, and evidence pack warnings. That makes the recommendation loop auditable, but the recommendation quality is still deterministic and template-driven.

The strategy expects Harness Builder to behave as an AI Agent, especially when judging ambiguous enterprise codebase conditions. The next missing layer is semantic review: an LLM should inspect the maturity score, evidence pack, and deterministic candidates, then produce structured judgment about candidate usefulness, missing risks, weak rationale, and additional acceptance checks.

## Chosen Milestone

Implement **LLM Maturity Reviewer** as an explicit review capability.

The first version adds a structured LLM reviewer tool and review artifacts. It does not make default `improve` depend on DeepSeek, because default CI and local fast tests must remain deterministic. LLM review will be invoked explicitly by a new command or flag in the implementation plan.

## Product Decisions

1. LLM review is additive. It reviews and enriches candidates; it does not directly edit formal Harness assets.
2. LLM output must be strict JSON and Pydantic-validated.
3. If DeepSeek is unavailable or returns invalid output, the review command fails explicitly.
4. Default `improve` remains deterministic unless LLM review is explicitly requested.
5. Review artifacts live under `.ai/review/`, matching existing candidate-review conventions.

## Data Contract

Add `src/harness_builder_agent/schemas/maturity_review.py`.

```python
MaturityCandidateReview:
  candidate_id: str
  decision: support | revise | defer
  rationale: str
  risks: list[str]
  suggested_acceptance_checks: list[str]
  evidence_sources: list[str]

MaturityReviewReport:
  schema_version: str = "1.0"
  summary: str
  reviewer_model: str | None
  candidate_reviews: list[MaturityCandidateReview]
  missing_candidates: list[str]
  global_risks: list[str]
```

## Prompt Contract

Input:

- `MaturityReport`
- `MaturityEvidencePack`
- `ImprovementCandidateReport`

Output:

- One JSON object only.
- No Markdown wrapper.
- Every `candidate_id` must reference an existing candidate.
- `decision` must be one of `support`, `revise`, `defer`.
- The LLM may suggest missing candidates as strings, but must not invent file writes or claim assets were changed.

## Output Artifacts

```text
.ai/review/maturity-review.yaml
.ai/review/maturity-review.md
```

YAML is machine-consumed and schema-validated. Markdown is human review material with stable sections:

- `# Maturity Review`
- `## Summary`
- `## Candidate Reviews`
- `## Missing Candidates`
- `## Global Risks`

## Integration Shape

Preferred implementation:

- Add `review-maturity` CLI command.
- The command ensures `maturity-score.yaml`, `maturity-evidence.yaml`, and `improvement-candidates.yaml` exist by running `assess` / `improve` when needed.
- It calls the LLM reviewer and writes review artifacts.
- CLI trace records both artifacts.

This avoids silently adding LLM dependency to existing deterministic `improve`.

Future integration:

- `improve --with-llm-review` can call the same tool after the explicit command exists.
- Benchmark can later validate review artifacts when a profile requests LLM review.

## Assumptions

- Unit tests use mock LLM callers and do not require DeepSeek.
- Acceptance tests for real DeepSeek can be added later; missing key must fail, not skip.
- This milestone is about review intelligence, not candidate application or auto-promotion.

## Risks

- LLM may overreach and recommend formal edits. Prompt and schema constrain it to review-only output.
- LLM may hallucinate candidate ids. Parser should reject unknown candidate ids during reconciliation.
- Adding a new command expands CLI surface. The command is justified because it isolates LLM dependency from default deterministic flows.

## Acceptance Criteria

- New maturity review schema validates good payloads and rejects invalid decisions.
- Reviewer parser rejects invalid JSON, invalid schema, and unknown candidate ids.
- `review-maturity` writes YAML and Markdown review artifacts using a mock LLM in integration tests.
- Missing DeepSeek config fails explicitly when no mock caller is supplied.
- Default `improve` tests remain deterministic.
- Focused tests and fast regression pass.
