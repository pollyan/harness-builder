# Goal Mode Retrospective Hardening Design

## Background

The recent goal-mode prompt was incomplete for several rounds. A retrospective audit found no major product-direction drift: recent work still aligns with maturity-driven existing-Harness maintenance, review-only self-improve, prompt centralization, and removal of the Builder-owned `run` runtime.

The audit did find contract and traceability gaps that could let future iterations drift:

- existing-Harness `init` status still compresses Experience / review signals into one count.
- workflow recommendation parsing accepts defaulted schema fields that the LLM did not explicitly return.
- maturity review artifacts lack an explicit review-only status and Markdown review boundary.
- guided maintenance tests do not snapshot all formal Harness assets.
- docs have stale status text around the guided init todo and standalone `recommend-workflow`.
- the larger evidence-source whitelist problem needs its own focused design.

## Current State Gap Analysis

| Gap | Risk | Decision |
| --- | --- | --- |
| Existing Harness status summary is too coarse | Maintainer cannot see pending improvements, review candidates, workflow recommendations, governance decisions, task-run availability, or review package status before choosing an action | Add a read-only structured status block using existing schema-validated artifacts |
| Workflow recommendation defaults mask missing LLM keys | LLM can omit `schema_version` or `review_status` and still pass schema via defaults | Require explicit top-level keys in the parser and prompt template |
| Maturity review lacks review-only contract | Review artifact is less auditable than workflow recommendation, candidate governance, and self-improve package | Add `review_status`, Markdown `## Review Boundary`, prompt contract, and benchmark check |
| Formal asset snapshot is incomplete | Guided actions could accidentally overwrite formal Guides not included in tests | Snapshot all formal core, guide, sensor, skill, and config assets by allowlisted paths |
| Todo/README drift | Next gap analysis can be misled by stale todo text | Update docs to reflect completed guided actions and standalone `recommend-workflow` |
| Evidence source whitelist is broad | LLM can cite unknown `.ai/` paths | Record as a new todo; do not combine with this hardening slice |

## Goals

- Strengthen review-only machine contracts without changing formal asset application semantics.
- Improve existing-Harness guided status transparency without scanning, refreshing, or writing files on `exit`.
- Tighten regression tests around guided actions not overwriting formal assets.
- Make the retrospective remediation visible in docs and evolution log.

## Non-Goals

- No guided apply implementation.
- No evidence-source whitelist implementation in this slice.
- No new machine-output schema except adding a review-only field to `MaturityReviewReport`.
- No changes to Runtime ownership or `.ai/task-runs` generation.

## Design

### Existing Harness Status Summary

`interactive_init.py` will replace the single `待处理 Experience / 候选信号：N` line with a short read-only status block:

- pending improvements
- asset candidates
- candidate governance decisions
- maturity reviews
- workflow recommendations
- runtime task runs
- self-improve package status
- human-input-needed status
- benchmark schema/content failed checks from the latest persisted report

The status block reads existing files only. It validates `ExperienceIndex`, `BenchmarkReport`, and `SelfImprovePackageManifest` where applicable. Missing files must be shown as missing, not converted into successful zeroes.

### Workflow Recommendation Explicit Keys

The workflow router parser will reject LLM JSON that omits any required top-level key:

`schema_version`, `task_id`, `task_brief`, `recommended_workflow`, `matched_rule_ids`, `risk_level`, `confidence`, `rationale`, `required_guides`, `required_sensors`, `human_confirmation_required`, `review_status`, `evidence_sources`.

The prompt will include the same full JSON template.

### Maturity Review Boundary

`MaturityReviewReport` will include:

`review_status: "pending_harness_maintainer_review"`

The LLM parser will require the review status key explicitly. The Markdown writer will add `## Review Boundary`, and benchmark will require that section.

### Test Hardening

The formal asset snapshot helper will include all formal Harness assets that guided maintenance actions must not overwrite, including architecture guide and task templates.

### Follow-Up Todo

The evidence source whitelist issue will be recorded as a separate todo because it affects multiple LLM tools and benchmark semantics.

## Acceptance Criteria

- A workflow recommendation LLM response missing explicit `review_status` fails parsing.
- A maturity review LLM response missing explicit `review_status` fails parsing.
- `review-maturity` writes YAML with `review_status` and Markdown with `## Review Boundary`.
- Benchmark fails maturity review Markdown that lacks `## Review Boundary`.
- Existing guided `init` exit output shows structured Experience / review status fields and still does not scan or write formal assets.
- Guided action tests snapshot all formal assets in the generated Harness.
- README, guided init todo, evolution log, and a follow-up todo are updated.
