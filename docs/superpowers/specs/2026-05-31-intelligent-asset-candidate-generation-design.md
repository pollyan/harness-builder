# Intelligent Asset Candidate Generation Design

## Context

This is the fifth autonomous milestone in the strategy-guided loop.

North Star reference:

- `docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`
- `4.1 Core Harness 与 Improvement System`
- `6.5 Experience & Self-Improve：经验沉淀与自我演进`
- `6.6 Maturity & Evolution：成熟度评估与演进路径`

Previous milestones established:

- structured maturity scoring;
- deterministic maturity evidence;
- maturity-driven improvement candidates;
- explicit LLM maturity review.

## Current State Gap Analysis

The system can now identify maturity gaps and review improvement candidates semantically. The next missing capability is turning those reviewed recommendations into concrete draft Harness asset changes.

Current review artifacts explain what should improve, but they do not produce structured candidate Guides, Sensors, or Workflow policy drafts that a Harness Maintainer can review and apply later.

The strategy requires Experience & Self-Improve to feed Guides, Sensors, Workflow, Harness Mapping, and Maturity. This milestone implements the next step in that chain while preserving the boundary that formal Harness assets are not changed automatically.

## Chosen Milestone

Implement **Intelligent Asset Candidate Generation** as an explicit LLM-powered command.

The command consumes:

- `.ai/maturity-score.yaml`
- `.ai/maturity-evidence.yaml`
- `.ai/improvement-candidates.yaml`
- `.ai/review/maturity-review.yaml`

It writes:

```text
.ai/review/asset-candidates.yaml
.ai/review/asset-candidate-guides.md
.ai/review/asset-candidate-sensors.md
.ai/review/asset-candidate-workflows.md
```

## Product Decisions

1. The feature is opt-in through a new command: `generate-asset-candidates`.
2. LLM output is strict JSON and Pydantic-validated.
3. Candidates are drafts only. They do not overwrite `.ai/guides`, `.ai/sensors`, `.ai/skills`, or `.ai/harness-config.yaml`.
4. Each draft links back to a reviewed improvement candidate or missing candidate from maturity review.
5. Draft Markdown files are grouped by asset kind for Harness Maintainer review.
6. Default `init`, `assess`, `improve`, and `benchmark` remain deterministic.

## Data Contract

Add `src/harness_builder_agent/schemas/asset_candidate.py`.

```python
AssetCandidateDraft:
  id: str
  kind: guide | sensor | workflow_policy
  source_candidate_id: str | None
  source_review_decision: support | revise | defer | missing
  suggested_path: str
  title: str
  rationale: str
  draft_content: str
  evidence_sources: list[str]
  acceptance_checks: list[str]
  risk_level: low | medium | high
  review_status: pending_harness_maintainer_review

AssetCandidateReport:
  schema_version: str = "1.0"
  source: str = "llm_maturity_review"
  candidates: list[AssetCandidateDraft]
```

## Prompt Contract

Input:

- maturity score;
- maturity evidence pack;
- improvement candidates;
- maturity review report.

Output:

- one JSON object only;
- each candidate must have `kind`, `suggested_path`, `draft_content`, `evidence_sources`, and `acceptance_checks`;
- `source_candidate_id` must reference an existing improvement candidate unless the candidate is derived from `missing_candidates`;
- `suggested_path` must be under `.ai/`;
- output must explicitly keep `review_status` as `pending_harness_maintainer_review`.

The LLM may propose draft content, but Python validates the schema and writes only review files.

## Integration Shape

Add:

- `llm_asset_candidate_generator.py` for prompt, parsing, and candidate-id validation.
- `generate_asset_candidates.py` for orchestration and file writing.
- `generate-asset-candidates` CLI command.

The command ensures prerequisite files exist:

1. run `assess` if maturity score/evidence is missing;
2. run `improve` if improvement candidates are missing;
3. run `review-maturity` if maturity review is missing.

Then it invokes LLM asset candidate generation and writes artifacts.

## Assumptions

- Unit and integration tests use mock LLM callers and do not require DeepSeek.
- Real DeepSeek acceptance remains covered by existing full acceptance policy and can be expanded later.
- The first version does not implement candidate application, approval, or merge into formal Harness assets.

## Risks

- LLM may generate overly broad drafts. Schema requires source evidence, acceptance checks, risk level, and pending review status.
- LLM may reference unknown candidate ids. Parser rejects unknown ids.
- Reusing existing `candidate-guides.md` names could clobber init review files, so this milestone writes `asset-candidate-*` files instead.

## Acceptance Criteria

- Asset candidate schema validates good payloads and rejects invalid kinds/review status.
- LLM parser rejects invalid JSON, invalid schema, unknown `source_candidate_id`, and non-`.ai/` suggested paths.
- `generate-asset-candidates` writes YAML plus guide/sensor/workflow Markdown review files using a mocked LLM.
- CLI trace records all generated artifacts.
- No formal `.ai/guides`, `.ai/sensors`, `.ai/skills`, or `.ai/harness-config.yaml` file is changed by this command.
- Focused tests and fast regression pass.
