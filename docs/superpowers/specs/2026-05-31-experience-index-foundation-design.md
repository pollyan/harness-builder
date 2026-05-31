# Experience Index Foundation Design

## Context

This is the sixth autonomous milestone in the strategy-guided loop.

North Star reference:

- `docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`
- `6.5 Experience & Self-Improve：经验沉淀与自我演进`
- `6.6 Maturity & Evolution：成熟度评估与演进路径`

Previous milestones created maturity scoring, evidence, deterministic improve, LLM review, and intelligent asset candidate generation.

## Current State Gap Analysis

The strategy defines Experience & Self-Improve as a persistent project-level learning layer with these files:

```text
.ai/experience/project-experience.md
.ai/experience/repair-patterns.md
.ai/experience/sensor-feedback.md
.ai/experience/team-preferences.md
.ai/experience/pending-improvements.md
.ai/experience/deprecated-experience.md
```

Current implementation only writes `pending-improvements.md`. Maturity evidence records only a pending improvement count. There is no machine-readable index showing which experience assets exist, which review/candidate sources contributed to them, or whether runtime task-run evidence is present.

This blocks later Experience Integration because task-run ingestion and candidate review need a stable place to accumulate and audit experience state.

## Chosen Milestone

Implement **Experience Index Foundation**.

The milestone adds:

```text
.ai/experience/experience-index.yaml
```

and ensures the full first-stage Markdown experience file set exists during initial asset generation and after improvement / asset-candidate generation.

## Product Decisions

1. The first index is deterministic and schema-validated.
2. It does not ingest runtime task-runs yet; it records whether `.ai/task-runs` exists.
3. It does not promote candidates into formal Guides/Sensors/Workflow assets.
4. It treats review and candidate files as experience sources.
5. Markdown experience files use stable sections but can remain sparse until real runtime evidence is available.

## Data Contract

Add `src/harness_builder_agent/schemas/experience_index.py`.

```python
ExperienceSource:
  path: str
  kind: pending_improvements | maturity_review | asset_candidates | runtime_task_runs | manual_experience
  item_count: int

ExperienceIndex:
  schema_version: str = "1.0"
  experience_files: dict[str, bool]
  sources: list[ExperienceSource]
  pending_improvement_count: int
  asset_candidate_count: int
  maturity_review_count: int
  runtime_task_run_count: int
  warnings: list[str]
```

## Output Files

Generated or preserved:

```text
.ai/experience/project-experience.md
.ai/experience/repair-patterns.md
.ai/experience/sensor-feedback.md
.ai/experience/team-preferences.md
.ai/experience/pending-improvements.md
.ai/experience/deprecated-experience.md
.ai/experience/experience-index.yaml
```

Stable Markdown sections:

- `# Project Experience`
- `# Repair Patterns`
- `# Sensor Feedback`
- `# Team Preferences`
- `# Deprecated Experience`

## Integration Shape

Add `src/harness_builder_agent/tools/experience_index.py`:

- `ensure_experience_files(ai)` creates missing Markdown files without overwriting existing content.
- `build_experience_index(ai)` reads current `.ai` review and experience artifacts and returns `ExperienceIndex`.
- `write_experience_index(ai, trace=None)` writes `.ai/experience/experience-index.yaml` and records trace artifact when available.

Wire it into:

- initial asset generation candidate writer;
- `generate_improvements`;
- `generate_asset_candidates`;

so the index stays current whenever candidate/review experience inputs change.

## Assumptions

- Runtime task-run ingestion remains future work because Harness Builder CLI does not generate `.ai/task-runs`.
- Counting candidate items from YAML is enough for this foundation; semantic experience extraction comes later.
- Existing project experience files must not be overwritten if a customer edits them.

## Risks

- An index can look like real experience even when it only reflects generated candidates. The index includes warnings when runtime task-runs are absent.
- Rewriting Markdown experience files could destroy customer notes. This milestone only creates missing files.

## Acceptance Criteria

- `ExperienceIndex` schema validates good payloads.
- Initial `init` writes all experience Markdown files and `experience-index.yaml`.
- `improve` refreshes `experience-index.yaml` and counts pending improvements.
- `generate-asset-candidates` refreshes `experience-index.yaml` and counts asset candidates.
- Benchmark validates `schema:experience-index`.
- Existing customer-edited experience Markdown is not overwritten by index refresh.
- Focused tests and fast regression pass.
