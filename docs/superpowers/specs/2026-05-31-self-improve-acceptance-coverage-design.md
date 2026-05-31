# Self-Improve Acceptance Coverage Design

## Current State Gap Analysis

North Star: Harness Builder should be a maturity-driven Self-Improve AI Coding Harness Builder. The previous milestone added the vertical `self-improve` command, which packages deterministic maturity gaps, LLM maturity review, and LLM asset candidate generation into review-only artifacts.

Current code has fast integration coverage for `self-improve`, but the real DeepSeek acceptance suite still only runs `init/assess/improve/benchmark`. That means the most important intelligent loop can pass with mocked LLMs while real LLM behavior is not exercised in the repository's highest-confidence local gate.

This gap came directly from the previous Self-Harness Improvement Gate and is recorded in `docs/todos/self-improve-acceptance-coverage.md`.

## Selected Milestone

Add real acceptance coverage for `self-improve` on one real benchmark repository.

This is a vertical user story: "As a Harness Builder maintainer, when I run local full regression, at least one real repository proves that the maturity-driven self-improve package works with real DeepSeek output and remains review-only."

It is prioritized over new product behavior because acceptance coverage protects the intelligent loop from drifting behind mocked integration tests.

## Scope

The acceptance suite will:

1. Run the existing `init`, `assess`, and `improve` sequence for both real repositories.
2. Run `self-improve` for one selected real repository.
3. Assert `.ai/review/self-improve-package.yaml` exists and has `review_status: pending_harness_maintainer_review`.
4. Assert `.ai/review/asset-candidates.yaml` exists and all candidates stay review-only.
5. Run benchmark afterward and assert `content:self-improve-package` is present and passed for the repository that ran `self-improve`.
6. Keep asserting `.ai/task-runs` is not created.

Out of scope:

- Running `self-improve` for every real repository in this milestone.
- Changing schemas.
- Applying generated asset candidates.
- Making acceptance part of default GitHub CI.

## Decisions And Responses

Question: Which repository should run `self-improve`?

Decision: Run it on `RuoYi-Vue` (`java-spring`) first. It gives one real LLM path through the command while keeping local full regression cost bounded.

Question: Should acceptance require benchmark `status: passed` after self-improve?

Decision: No. Existing acceptance allows benchmark to return `failed` when hard gate command evidence is legitimately insufficient. The new requirement is narrower: if the self-improve package exists, its benchmark check must be present and pass.

Question: Should missing DeepSeek credentials skip the test?

Decision: No. Existing acceptance policy says missing credentials must fail explicitly, not skip.

Question: Should acceptance tolerate empty asset candidates?

Decision: It should tolerate an empty candidates list only if the YAML schema remains valid and review-only. However, real value is stronger when the LLM returns at least one draft; the test will assert the artifact is schema-valid and review-only without forcing candidate count > 0.

## Edge Cases And Failure Modes

- Real DeepSeek returns no candidates: acceptance still validates package and review-only boundary.
- Real DeepSeek returns invalid JSON or schema-invalid candidates: acceptance fails, correctly exposing LLM contract drift.
- Benchmark fails for hard gate evidence: acceptable if the self-improve package check itself passes.
- Runtime task directory appears: acceptance fails because Builder must not create `.ai/task-runs`.
- Self-improve command times out: acceptance fails with real stderr/stdout context.
- Real DeepSeek returns JSON that is syntactically valid but misses required schema fields: acceptance fails; root cause is treated as LLM contract/prompt drift, not as a reason to relax schema.

## Debugging Update

The first GREEN attempt exposed a real DeepSeek contract failure in `self-improve`: the asset candidate generator returned a JSON object, but candidate objects missed required `AssetCandidateDraft` fields such as `id`, `title`, and `rationale`. A direct diagnostic call with a longer timeout confirmed the response was valid JSON but schema-invalid.

Response: keep the Pydantic schema strict and tighten the asset-candidate prompt so it enumerates every candidate field, includes a full object template, and limits the output to at most five concise review-only candidates. This preserves the LLM/Python split: LLM proposes candidates; Python validates schema and rejects drift.

The next acceptance runs exposed related real DeepSeek issues in the earlier maturity review stage: one response was JSON-invalid and another returned empty `content` despite the API call succeeding. Diagnostic calls showed DeepSeek can return valid `content` plus `reasoning_content`, so the empty response is treated as a transient API/model output anomaly rather than a reason to parse reasoning text.

Response: align the maturity review prompt with the asset-candidate prompt by adding a full JSON template, required candidate review keys, and explicit no-markdown/no-trailing-comma wording. Add a bounded DeepSeek client retry for empty `content`; after the retry it still fails explicitly with non-sensitive metadata.

Prompt management update: because multiple intelligent LLM functions now exist and real acceptance failures came directly from prompt contract drift, prompt centralization is required in this milestone. All machine-consumed LLM prompts are moved under `src/harness_builder_agent/prompts/`; Python modules only load prompt sections and append structured payload JSON.

## Acceptance Criteria

- `tests/acceptance/test_real_repositories_e2e.py` runs `self-improve` for `RuoYi-Vue`.
- The test validates `SelfImprovePackageManifest`.
- The test validates `AssetCandidateReport`.
- The test asserts all asset candidates are `pending_harness_maintainer_review`.
- The benchmark report contains `content:self-improve-package` and that check passes.
- Unit tests assert the asset-candidate prompt declares the complete candidate schema and output limit.
- Unit tests assert the maturity-review prompt declares the complete review schema/template and that DeepSeek empty content is retried once before explicit failure.
- Unit tests assert all known prompt assets are loadable and `tools/llm_*.py` no longer embeds machine prompt contracts.
- The old todo is archived.
- Fast regression and full regression pass.

## Assumptions

- `.benchmarks/RuoYi-Vue` exists in the local environment used for full regression.
- DeepSeek credentials are available during full regression, as already required.
- One real repository is enough for this milestone; broadening to both repositories can be a later cost/coverage decision.

## Risks

- Full regression runtime and DeepSeek cost increase. Mitigation: only one real repo runs `self-improve`.
- Real LLM output can be variable. Mitigation: assert schema/review boundary, not exact candidate text.
- The test can expose real prompt or schema fragility. That is desirable for this milestone.
