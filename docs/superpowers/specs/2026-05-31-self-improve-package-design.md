# Self-Improve Package Design

## Current State Gap Analysis

North Star: `docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md` describes Harness Builder as a maturity-driven Self-Improve Harness Agent. The relevant capability modules are Experience & Self-Improve and Maturity & Evolution: the system should turn maturity gaps, task/review evidence, and LLM judgment into reviewable Harness improvement candidates without silently changing formal project rules.

Current code already has the ingredients:

- `assess` writes `.ai/maturity-score.yaml` and `.ai/maturity-evidence.yaml`.
- `improve` writes deterministic `.ai/improvement-candidates.yaml`, `.ai/evolution-plan.md`, and `.ai/experience/pending-improvements.md`.
- `review-maturity` asks the LLM to review improvement candidates.
- `generate-asset-candidates` asks the LLM to draft review-only Guide / Sensor / Workflow policy candidates.
- `summarize-experience` can produce review-only Experience findings.
- `benchmark` validates optional review artifacts when present.

The gap is product-level, not a missing low-level primitive: a Harness Maintainer currently has to know and manually sequence several commands to get one maturity-driven self-improvement package. That makes the intelligent loop feel fragmented and reduces the value of the existing LLM stages.

## Selected Milestone

Add a `self-improve` CLI command that generates one review-only self-improvement package for a Harness repository.

This is a vertical user story: "As a Harness Maintainer, I can ask Harness Builder to produce a maturity-driven self-improvement package in one command, then review the proposed changes without formal assets being modified."

It is selected over another schema-only or prompt-only change because it exposes existing intelligence as an end-to-end workflow, advances the North Star directly, and can be validated with integration tests using mocked LLM calls.

## Scope

`self-improve` will orchestrate existing capabilities:

1. Ensure maturity assessment exists.
2. Generate deterministic improvement candidates.
3. Run LLM maturity review.
4. Generate review-only asset candidates from that review.
5. Refresh Experience index and maturity evidence through the existing called tools.
6. Write a manifest and Markdown summary for the package.
7. Record generation trace artifacts from the CLI.

Out of scope for this milestone:

- Applying candidates into formal Guides, Sensors, Workflow Skills, or `harness-config.yaml`.
- Creating `.ai/task-runs`.
- Adding a dashboard.
- Changing LLM prompts beyond what is required to orchestrate existing commands.
- Running true Runtime workflows.

## Proposed Artifacts

Machine-readable manifest:

```text
.ai/review/self-improve-package.yaml
```

Human-readable summary:

```text
.ai/review/self-improve-package.md
```

The manifest will include:

- `schema_version`
- `package_id`
- `review_status`
- `generated_artifacts`
- `candidate_counts`
- `maturity`
- `next_actions`
- `warnings`

The summary will include stable sections:

- `# Self-Improve Package`
- `## Maturity Snapshot`
- `## Generated Artifacts`
- `## Candidate Counts`
- `## Next Actions`
- `## Review Boundary`

## Decisions And Responses

Question: Should this command apply high-confidence candidates automatically?

Decision: No. The current product boundary says high-risk formal Harness changes must remain candidates/review status. The new command packages reviewable outputs only.

Question: Should `summarize-experience` be part of the default package?

Decision: No for this milestone. It is useful but optional and LLM-costly. The default self-improve loop should produce maturity review plus asset candidates. Future work can add `--include-experience-summary`.

Question: Should the command succeed without LLM credentials?

Decision: No. It invokes LLM review and LLM asset candidate generation. If the configured LLM is unavailable, the existing LLM stages must fail explicitly.

Question: Does this conflict with removing `run`?

Decision: No. The command only operates on project-level Harness assets and review artifacts. It must not create `.ai/task-runs` or execute a Runtime workflow.

Question: Is this too broad for one milestone?

Decision: It is a small orchestration slice over existing tested commands plus a manifest schema. It does not introduce candidate application or new prompt behavior.

## Edge Cases And Failure Modes

- Missing `.ai` assets: delegated tools may run `assess` / `improve` as needed or fail with existing explicit errors.
- LLM fails or returns invalid schema: the command fails; no deterministic fallback should pretend success.
- Asset candidates are empty: the package still writes counts and next actions, making the review result explicit.
- Existing formal assets must not change except derived assessment / review files already owned by the loop.
- Existing `.ai/task-runs` from a host Runtime may be counted by evidence tools, but the command must not create the directory.
- Benchmark should validate the generated optional review artifacts.

## Acceptance Criteria

- `harness-builder-agent self-improve --repo <repo>` exists.
- With mocked LLM reviewers, it writes:
  - `.ai/improvement-candidates.yaml`
  - `.ai/review/maturity-review.yaml`
  - `.ai/review/asset-candidates.yaml`
  - `.ai/review/self-improve-package.yaml`
  - `.ai/review/self-improve-package.md`
- The manifest validates through a Pydantic schema.
- The manifest includes candidate counts and paths to generated artifacts.
- Formal Guide / Sensor / Workflow assets are not modified by the package generation.
- `.ai/task-runs` is not created.
- CLI trace records self-improve stages and artifacts.
- `benchmark` passes on a repo with the generated package.

## Assumptions

- Existing LLM stages are the source of intelligence; this milestone should not duplicate their prompt logic.
- Review-only status remains `pending_harness_maintainer_review`.
- The command can be tested with monkeypatched LLM functions at integration level.
- Full DeepSeek acceptance can remain covered by existing acceptance flows unless this command is later added to acceptance.

## Risks

- Orchestration can hide which stage failed. Mitigation: use trace events for each major stage and preserve underlying exceptions.
- The package may be perceived as applying changes. Mitigation: summary and manifest explicitly state review-only boundary.
- Running multiple LLM calls can be costly. Mitigation: this command is explicit and not part of `init` or `benchmark`.

## Self-Harness Notes

After implementation, update docs/engineering only if the new command changes stable CLI/product rules. Tests must assert schema, content, cross-file references, review-only status, and no `.ai/task-runs` creation rather than only file existence.
