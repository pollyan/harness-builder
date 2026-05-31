# Maturity Model v2 Design

## Context

This milestone starts the strategy-guided automatic execution loop from `docs/strategy/`.

North Star reference:

- `docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`
- Section `6.6 Maturity & Evolution：成熟度评估与演进路径`
- Section `4.1 Core Harness 与 Improvement System`

Current engineering constraints:

- `AGENTS.md`
- `docs/engineering/architecture.md`
- `docs/engineering/init-workflow.md`
- `docs/engineering/testing-strategy.md`

## Current State Gap Analysis

The strategy document defines Maturity & Evolution as a roadmap engine. It should identify maturity gaps across Guides, Sensors, Workflow, Risk Control, Repair Loop, Observability, Experience, Verification Sophistication, and Governance & Auditability. It should also explain blockers and next-level requirements.

The current implementation is still a POC scorecard:

- `src/harness_builder_agent/schemas/maturity_report.py` only stores `overall_level`, flat `dimension_scores`, top-level evidence, blockers, and next steps.
- `src/harness_builder_agent/tools/assess_maturity.py` computes a small set of deterministic levels and writes a plain report.
- `src/harness_builder_agent/tools/generate_improvements.py` can only generate broad fixed candidates because the maturity score has no per-dimension blockers or next-level requirements.
- Initial `.ai/maturity-score.yaml` written by `asset_writers/reports.py` has the same flat shape.

This blocks the later intelligent improve loop. An LLM maturity reviewer or maturity-driven improve command needs a structured maturity model before it can make auditable recommendations.

## Chosen Milestone

Implement **Maturity Model v2** as the first autonomous milestone.

The goal is to make `maturity-score.yaml` a structured roadmap input while preserving existing top-level fields for compatibility.

This milestone does not introduce LLM maturity review yet. It creates the deterministic schema and evidence surface that the later LLM reviewer will consume.

## Alternatives Considered

### Option A: Add LLM maturity review immediately

Rejected for this milestone. It would add a new LLM call before the deterministic maturity contract exists, making tests and failure modes too broad.

### Option B: Only change `improve` candidates

Rejected. `improve` would still be forced to infer blockers from flat strings. That would preserve the current weak maturity model.

### Option C: Extend maturity schema and deterministic assessor first

Selected. It is smaller, testable, aligned with the strategy document, and creates the required input for later intelligent review and maturity-driven improve.

## Product Decisions

1. Keep `overall_level`, `dimension_scores`, `evidence`, `blocking_reasons`, and `recommended_next_steps` for backward compatibility.
2. Add structured `dimensions` with per-dimension level, evidence, blockers, next-level requirements, and confidence.
3. Add `blocking_caps` to encode strategy-level cap rules such as “no executable sensors caps overall at L1”.
4. Add `target_next_level` so `improve` can plan against a specific maturity step.
5. Treat runtime `.ai/task-runs` as optional external Runtime evidence. Harness Builder CLI does not generate it.
6. Keep the first implementation deterministic. LLM maturity review is a later milestone.

## Data Contract

`MaturityReport` remains the machine schema for `.ai/maturity-score.yaml`.

New nested models:

```python
MaturityEvidence:
  source: str
  summary: str

MaturityBlocker:
  id: str
  reason: str
  prevents_level: MaturityLevel | None

MaturityNextStep:
  id: str
  target_dimension: str
  action: str
  priority: critical | high | medium | low
  expected_lift: str | None

MaturityDimensionReport:
  level: MaturityLevel
  evidence: list[MaturityEvidence]
  blockers: list[MaturityBlocker]
  next_level_requirements: list[str]
  confidence: Confidence

MaturityBlockingCap:
  id: str
  reason: str
  max_level: MaturityLevel
  active: bool
  evidence: list[str]
```

`MaturityReport` adds:

```python
target_next_level: MaturityLevel | None
dimensions: dict[str, MaturityDimensionReport]
blocking_caps: list[MaturityBlockingCap]
next_steps: list[MaturityNextStep]
```

The existing `recommended_next_steps: list[str]` stays as a human-readable summary.

## Dimension Set

The first v2 implementation covers the strategy dimensions:

- `guides`
- `sensors`
- `workflow`
- `risk_control`
- `repair_loop`
- `observability`
- `experience`
- `verification_sophistication`
- `governance_auditability`

## Deterministic Assessment Rules

Initial deterministic levels:

- `guides`: `L2` when structured guide sections exist, otherwise `L1` if guide assets are expected or present.
- `sensors`: `L2` when command catalog has commands, otherwise `L0`.
- `workflow`: `L2` when workflow skills and config workflows exist, otherwise `L1` or `L0`.
- `risk_control`: `L1` when inventory contains risk areas or candidate confirmation assets, otherwise `L0`.
- `repair_loop`: `L0` because Harness Builder no longer owns task runtime execution.
- `observability`: `L1` when `.ai/runs` generation trace exists, otherwise `L0`.
- `experience`: `L1` when pending improvements exist, otherwise `L0`.
- `verification_sophistication`: `L1` when any validation command exists, otherwise `L0`.
- `governance_auditability`: `L1` when generation trace and decision log exist, otherwise `L0`.

Overall level remains conservative:

- No commands caps overall at `L0`.
- Commands without workflow skills caps at `L1`.
- Commands plus workflow skills and config workflows produce current `L2`.
- This milestone does not produce `L3` or `L4`; those require Runtime execution evidence and self-improve feedback.

## Output Changes

`maturity-score.yaml` will include both legacy summary fields and v2 structured fields.

`maturity-report.md` will keep stable sections:

- `## 评分维度`
- `## 证据`
- `## 阻断原因`
- `## 推荐下一步`

It will add:

- `## 维度详情`
- `## 下一等级要求`

## Testing Strategy

TDD will cover:

1. `MaturityReport` schema accepts structured dimensions, blockers, caps, and typed next steps.
2. `assess` writes v2 `dimensions` for all strategy dimensions.
3. `assess` writes per-dimension evidence, blockers, next-level requirements, and `target_next_level`.
4. Empty command catalog still lowers sensor maturity and activates a cap.
5. Initial asset writer emits schema-valid v2 maturity score.
6. Benchmark schema validation still passes with v2 score.

## Assumptions

- The first v2 contract can stay deterministic; later milestones add LLM review on top.
- `schema_version` can remain `1.0` for this backward-compatible extension because legacy top-level fields remain valid.
- Runtime task artifacts are optional external evidence and are not generated by Harness Builder.

## Open Risks

- The deterministic levels are still coarse. This is acceptable because this milestone creates the contract surface, not the final intelligent reviewer.
- Existing `improve` will initially consume legacy fields. The next milestone should make it consume `dimensions`, `blocking_caps`, and `next_steps`.

## Acceptance Criteria

- `.ai/maturity-score.yaml` validates against the expanded `MaturityReport` schema.
- `assess` output includes all v2 dimensions and stable Markdown sections.
- Tests prove no-command repositories produce lower sensor maturity and an active cap.
- Existing init/e2e/benchmark flows still pass fast regression.
