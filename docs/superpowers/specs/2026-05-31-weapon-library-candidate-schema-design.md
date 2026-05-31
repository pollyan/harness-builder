# Weapon Library Candidate Schema Design

## Context

Harness Builder writes `.ai/experience/weapon-library-candidates.yaml` during initialization. This file records LLM scan-derived Guide/Sensor enhancement candidates and is consumed by benchmark, review Markdown writers, guided decisions, and downstream Experience evidence.

The current implementation builds the report as plain dictionaries. Benchmark checks only a few ad hoc keys (`schema_version`, `source`, non-empty `candidates`). That violates the repository rule that machine-consumed outputs must have Pydantic schemas and tests.

## Capability Module

- North Star module: Experience & Self-Improve.
- Supporting modules: Benchmark / Review Intelligence, Intelligent Asset Candidate Generation.

## Current State Gap

- `weapon-library-candidates.yaml` is required output and appears in benchmark.
- It has no dedicated schema under `src/harness_builder_agent/schemas/`.
- `build_llm_enhancement_candidates` returns `dict[str, Any]`, so invalid candidate statuses, missing evidence, or non-boolean confirmation flags are not rejected at construction time.
- `_llm_enhancement_checks` performs loose dict checks instead of schema validation.

## Assumptions And Decisions

- This milestone does not change the candidate generation strategy.
- Valid candidate types remain `guide` and `sensor` because current init enhancement candidates only cover candidate Guides and Sensors.
- Valid candidate status values are `candidate`, `confirmed`, and `rejected` because guided decisions can keep, accept, or reject candidates.
- All generated candidates remain human-reviewed before becoming formal Harness assets.
- Evidence is modeled as a non-empty list because candidate review must be auditable.

## Design

Add `src/harness_builder_agent/schemas/weapon_library_candidate.py` with:

- `WeaponLibraryCandidate`
  - `id: str`
  - `candidate_type: Literal["guide", "sensor"]`
  - `status: Literal["candidate", "confirmed", "rejected"]`
  - `title: str`
  - `rationale: str`
  - `evidence: list[str]`
  - `source: Literal["llm_scan_proposal"]`
  - `human_confirmation_required: bool`
  - `decision_notes: str | None = None`
- `WeaponLibraryCandidateReport`
  - `schema_version: "1.0"`
  - `source: "llm_scan_proposal"`
  - `candidates: list[WeaponLibraryCandidate]`

Update:

- `build_llm_enhancement_candidates` to return `WeaponLibraryCandidateReport` after validation.
- Markdown helper functions to accept the schema object.
- `write_candidate_assets` to dump the schema object with `model_dump`.
- `apply_candidate_decisions` to continue operating on dict payloads by converting the schema object at the caller boundary.
- benchmark `_llm_enhancement_checks` to parse `WeaponLibraryCandidateReport`.

## Testing

Add tests that fail before implementation:

- Schema contract rejects invalid candidate status.
- `build_llm_enhancement_candidates` returns a `WeaponLibraryCandidateReport`.
- Benchmark rejects invalid `weapon-library-candidates.yaml` status through schema validation.

Existing init and asset writer tests should continue to pass.

## Risks

- Changing return type from dict to Pydantic model can break writers that index the report as a dict. The implementation must update those call sites in the same milestone.
- Guided decision code currently mutates dict candidates. Keep that boundary dict-based to avoid broad refactoring.
- This is schema hardening only; it does not make candidate generation itself more intelligent.

## Acceptance Criteria

- `weapon-library-candidates.yaml` has a Pydantic schema and tests.
- Generation validates candidates before writing.
- Benchmark uses the schema instead of ad hoc dict checks.
- Existing init, benchmark, and asset writer tests pass.
- No `run` behavior or `.ai/task-runs` generation is introduced.
