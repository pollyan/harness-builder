# Maturity-Driven Improve Design

## Context

This is the third autonomous milestone in the strategy-guided loop.

North Star reference:

- `docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`
- `4.1 Core Harness 与 Improvement System`
- `6.5 Experience & Self-Improve：经验沉淀与自我演进`
- `6.6 Maturity & Evolution：成熟度评估与演进路径`

Previous milestones:

- `Maturity Model v2` added structured dimensions, blockers, caps, and next steps.
- `Maturity Evidence Pack` added `.ai/maturity-evidence.yaml` as deterministic input for review and improvement.

## Current State Gap Analysis

The strategy defines Harness Improvement System as:

```text
Scanner + Experience + Maturity + Recommendation
```

Current `improve` only reads `.ai/maturity-score.yaml` and emits a few generic candidates. It does not consume `.ai/maturity-evidence.yaml`, does not preserve a direct link to `next_steps` / `blocking_caps`, and does not give Harness Maintainers concrete acceptance checks for each proposed improvement.

That makes the output reviewable, but not yet maturity-driven enough. The next implementation should turn the structured maturity report and evidence pack into auditable improvement candidates.

## Chosen Milestone

Implement **Maturity-driven Improve**.

The milestone upgrades `harness-builder-agent improve` so it:

1. ensures maturity score and evidence pack exist;
2. reads both files through Pydantic schemas;
3. generates candidates from structured `next_steps`, active `blocking_caps`, and evidence pack warnings;
4. records target dimension, source next step, acceptance checks, and evidence inputs on every candidate;
5. keeps all formal Harness changes in candidate / pending review state.

## Product Decisions

1. This milestone remains deterministic. LLM semantic review is the next milestone.
2. `improve` may generate smarter candidates, but it must not directly edit formal Guides, Sensors, Workflow Skills, or config.
3. Every generated candidate must be traceable to maturity evidence: a next step, active cap, warning, or evidence input.
4. Candidate schema is extended with optional fields rather than replacing existing fields, preserving compatibility with current tests and assets.
5. Pending improvements remain Markdown in this milestone, but each item includes enough structured context for human review.

## Data Contract Changes

Extend `ImprovementCandidate`:

```python
target_dimension: str | None
source_next_step: str | None
source_blocking_cap: str | None
acceptance_checks: list[str]
evidence_sources: list[str]
```

Existing fields remain:

```python
id
candidate_type
suggested_target
rationale
evidence
confidence
human_confirmation_required
priority
```

## Improve Algorithm

Input:

- `.ai/maturity-score.yaml`
- `.ai/maturity-evidence.yaml`

Process:

1. If either file is missing, run `assess_maturity(repo)` so both are refreshed.
2. Load `MaturityReport` and `MaturityEvidencePack`.
3. For each high / medium priority `score.next_steps`, emit one candidate.
4. For each active blocking cap without an existing candidate, emit one candidate.
5. For evidence pack warnings that expose missing observability or benchmark context, emit one candidate.
6. Deduplicate by candidate id while preserving priority order.

Mapping:

| Dimension / cap | Candidate type | Target |
|---|---|---|
| `guides` | `guide_update` | `.ai/guides/project-context.md` |
| `sensors`, `verification_sophistication` | `sensor_update` | `.ai/sensors/verification.md` |
| `workflow`, `repair_loop`, `risk_control` | `workflow_policy_update` | `.ai/harness-config.yaml` |
| `observability`, `governance_auditability`, runtime audit cap | `maturity_action` | `.ai/runs/` or `.ai/task-runs/` |
| `experience` | `maturity_action` | `.ai/experience/pending-improvements.md` |

## Output

Existing outputs remain:

```text
.ai/improvement-candidates.yaml
.ai/evolution-plan.md
.ai/experience/pending-improvements.md
```

`improvement-candidates.yaml` becomes more useful for future LLM reviewer and Harness Maintainer review because each candidate includes the maturity gap, source, acceptance checks, and evidence sources.

## Assumptions

- Runtime-owned `.ai/task-runs` remains optional evidence. `improve` can recommend integrating runtime evidence but must not generate task-runs.
- The first version can use deterministic templates for candidate rationale and acceptance checks.
- LLM Maturity Reviewer will later consume the same maturity score and evidence pack to enrich or challenge these candidates.

## Risks

- Too many candidates can overwhelm maintainers. This milestone deduplicates and prioritizes candidates by maturity next steps and active caps.
- Deterministic recommendations may still be generic. That is acceptable here because this milestone creates the structured bridge that the next LLM reviewer will improve.
- Candidate schema growth can become noisy. Optional fields are limited to traceability and acceptance checks.

## Acceptance Criteria

- `ImprovementCandidate` validates the new optional traceability fields.
- `improve` rebuilds missing `.ai/maturity-evidence.yaml` through `assess`.
- `improvement-candidates.yaml` includes candidates linked to `target_dimension`, `source_next_step` or `source_blocking_cap`, `acceptance_checks`, and `evidence_sources`.
- `pending-improvements.md` and `evolution-plan.md` expose maturity dimensions and acceptance checks.
- benchmark still validates `improvement-candidates.yaml`.
- Focused tests and fast regression pass.
