# Human Confirmation Machine Contracts Design

## Context

`init` always writes `.ai/context-inputs.yaml` and `.ai/questionnaire.yaml`. Both files are listed as machine-consumed outputs in `docs/engineering/init-workflow.md`, but the implementation currently builds them as plain dictionaries. Benchmark validates `questionnaire.yaml` with ad hoc key checks and does not validate `context-inputs.yaml` with a Pydantic schema.

This leaves one of the first human-in-the-loop boundaries less strict than other Harness assets.

## Capability Module

- North Star module: Core Harness generation.
- Supporting modules: Governance & Auditability, Benchmark / Review Intelligence.

## Current State Gap

- `context-inputs.yaml` has no schema class.
- `questionnaire.yaml` has no schema class.
- `read_context_inputs` and `build_questionnaire` return unvalidated dictionaries.
- `write_human_confirmation_assets` writes these dictionaries directly.
- benchmark only checks `questionnaire.schema_version` and non-empty questions through dict access.

## Assumptions And Decisions

- This milestone does not change interactive behavior or add new questions.
- Functions may continue returning dictionaries to avoid broad call-site refactors, but they must validate through Pydantic before returning or writing.
- `context-inputs.yaml` may have an empty `contexts` list when no `--context` files are provided.
- `questionnaire.yaml` must always have at least one question.
- Valid confidence values reuse the existing `Confidence` literal.

## Design

Create `src/harness_builder_agent/schemas/human_confirmation.py`:

- `ContextInput`
  - `path: str`
  - `size_bytes: int >= 0`
  - `summary: str`
  - `truncated: bool`
- `ContextInputs`
  - `schema_version: "1.0"`
  - `contexts: list[ContextInput]`
- `QuestionnaireQuestion`
  - `interaction_type`
  - `interaction_id`
  - `question`
  - `options`
  - `confidence`
  - `reason`
- `Questionnaire`
  - `schema_version: "1.0"`
  - `questions: list[QuestionnaireQuestion]` with at least one item.

Update:

- `read_context_inputs` validates `ContextInputs`.
- `build_questionnaire` validates `Questionnaire`.
- `write_human_confirmation_assets` validates both payloads before writing.
- benchmark validates both schema files and keeps `content:human-confirmation` for required question ids and Markdown presence.

## Testing

Add tests for:

- Invalid context input size is rejected.
- Invalid questionnaire interaction type is rejected.
- `read_context_inputs` / `build_questionnaire` outputs validate through schema.
- benchmark includes `schema:context-inputs`.
- benchmark fails invalid persisted `questionnaire.yaml`.

## Risks

- Tightening schema may expose old invalid fixtures. Current generated shape is stable and should already satisfy the new schemas.
- Overly strict enum choices could block future interaction types. The schema should include current known types and can be extended intentionally when a new interaction type is added.

## Acceptance Criteria

- `context-inputs.yaml` and `questionnaire.yaml` have Pydantic schemas.
- Generation validates both machine payloads before writing.
- benchmark validates both persisted files with Pydantic schemas.
- Existing init, benchmark, and human confirmation tests pass.
- No `run` behavior or `.ai/task-runs` generation is introduced.
