# Centralized LLM Prompts Design

## Current State Gap Analysis

North Star modules: LLM-first repository understanding, LLM Maturity Reviewer, Intelligent Asset Candidate Generation, Experience Integration, Workflow Toolkit Evolution, and Benchmark / Review Intelligence.

Current code has real intelligent functions, but prompt assets are inconsistent: `llm_scan_analyzer` loads `src/harness_builder_agent/prompts/llm_first_scan_v2.md`, while maturity review, asset candidate generation, experience summary, and workflow recommendation still embed large prompt contracts inside `tools/llm_*.py`. This makes prompt review, drift detection, and schema contract hardening harder than it needs to be.

The gap is now material, not future-looking: real DeepSeek acceptance exposed prompt contract issues in both maturity review and asset candidate generation. Centralizing prompts is therefore part of making the intelligent layer observable and maintainable, not cosmetic cleanup.

## Selected Milestone

Move every machine-consumed LLM prompt into `src/harness_builder_agent/prompts/` and make prompt asset loading a shared helper.

This is a vertical maintainability slice: Harness Builder keeps the same CLI/user behavior, but every intelligent LLM capability now has a reviewable prompt asset, a stable loader contract, and tests preventing new inline prompt drift.

## Scope

- Add a shared prompt loader that reads Markdown prompt assets with `## System Message` and `## User Message`.
- Keep Python modules responsible for payload construction, schema validation, and reconciliation.
- Move these prompt contracts into prompt assets:
  - scan proposal, already externalized.
  - maturity review.
  - asset candidate generation.
  - experience summary.
  - workflow recommendation.
- Update engineering docs so prompt centralization is a current rule.
- Add tests that verify prompt assets exist, include required sections, and LLM tool modules no longer embed the long machine-consumed prompt contracts.

Out of scope:

- Changing schemas.
- Changing CLI outputs beyond prompt-driven LLM wording.
- Applying generated review-only assets.
- Adding dynamic prompt templating beyond loading static Markdown and appending JSON payloads.

## Decisions And Tradeoffs

- Decision: Use Markdown prompt assets instead of Python string constants. This matches the existing scan prompt pattern and gives maintainers reviewable files.
- Decision: Keep payload JSON assembly in Python. This preserves Pydantic/schema ownership in code and avoids fragile text templating for structured data.
- Decision: Introduce one shared loader. This removes copy-pasted resource loading and makes malformed prompt assets fail explicitly.
- Decision: Treat centralization as a hard rule in `docs/engineering/llm-contracts.md`, not a future suggestion.

## Edge Cases And Failure Modes

- Prompt asset missing or malformed: loader raises `ValueError` with the prompt name.
- Prompt file lacks System/User sections: unit tests and loader fail.
- Package data misses prompt assets: existing `pyproject.toml` already includes `prompts/*.md`; tests read assets through importlib resources.
- New LLM module adds inline prompt later: unit test scanning `src/harness_builder_agent/tools/llm_*.py` fails.

## Acceptance Criteria

- All `build_*_messages` functions load prompt text from `src/harness_builder_agent/prompts/`.
- `src/harness_builder_agent/tools/` no longer contains the long machine-consumed prompt contracts as inline triple-quoted strings.
- Prompt asset tests cover section parsing and known prompt filenames.
- Existing prompt content assertions for maturity review, asset candidate generation, experience summary, workflow recommendation, and scan still pass.
- Targeted unit tests and fast regression pass.
- Engineering docs and evolution log record prompt centralization as a current rule.

## Assumptions

- `importlib.resources.files("harness_builder_agent")` remains compatible with editable installs and packaged installs because `pyproject.toml` includes `prompts/*.md`.
- Prompt wording changes should be minimal: move content first, do not redesign every prompt in this milestone.

## Risks

- Moving prompt text can accidentally change whitespace. Tests assert key contract phrases, not exact full text.
- Centralizing prompt files increases the number of package data assets. Mitigation: load through importlib resources in tests.
