# Human-Centered Guided Init Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Chinese, human-centered guided `init` flow with explanatory scan summary, open supplements, candidate review, workflow preview, final summary, and summary-stage backtracking.

**Architecture:** Keep the existing scan and asset writer pipeline. Add focused UI helper functions under `interactive_init.py`, extend `InteractionDecisions` with workflow/candidate edit state, and apply safe scan overrides before asset writing. Preserve non-interactive behavior.

**Tech Stack:** Python 3.11, Typer, Pydantic, PyYAML, Pytest.

---

## File Structure

- Modify `src/harness_builder_agent/schemas/interaction_decision.py`: add `edited` candidate decision and workflow confirmation schema.
- Modify `src/harness_builder_agent/tools/interaction_decisions.py`: support edited decisions and richer markdown.
- Modify `src/harness_builder_agent/tools/interactive_init.py`: implement the guided UX state machine and scan override application.
- Modify `src/harness_builder_agent/tools/asset_writers/guides.py`: include scan correction notes and workflow confirmation in generated guide context.
- Modify `tests/unit/test_interaction_decisions.py`: cover edited candidate and workflow confirmation.
- Modify `tests/integration/test_init_on_fixture_projects.py`: cover guided Chinese UX, scan correction, candidate decisions, workflow preview, summary backtracking, and non-interactive compatibility.
- Modify `README.md` and `docs/todos/guided-init-human-centered-cli.md`: document the improved guided mode and mark the todo implemented after verification.

## Task 1: Extend Interaction Decisions Schema

- [ ] Write failing tests for edited candidate decisions and workflow confirmation.
- [ ] Run `pytest tests/unit/test_interaction_decisions.py -q` and verify failure.
- [ ] Add `edited` to `CandidateDecisionStatus`.
- [ ] Add `WorkflowConfirmation` with `shown_workflows`, `confirmed`, and `notes`.
- [ ] Add `workflow_confirmation` to `InteractionDecisions`.
- [ ] Update markdown rendering to include workflow and edited decisions.
- [ ] Re-run the unit test.

## Task 2: Guided Init Human-Centered UI

- [ ] Write failing integration test for guided happy path showing “扫描发现”, “主要技术栈”, “团队规则”, “建议生成的规则”, “建议生成的传感器”, “推荐工作流”, and “最终确认”.
- [ ] Write failing integration test where user inputs scan correction notes and verifies generated guides and interaction decisions contain the notes.
- [ ] Write failing integration test where user chooses stack correction and verifies `project-inventory.json` uses the override.
- [ ] Write failing integration test where final summary receives `back`, user edits team rules, then confirms.
- [ ] Run targeted integration tests and verify RED.
- [ ] Implement sectioned Chinese output helper functions in `interactive_init.py`.
- [ ] Implement scan supplement prompt with `stack=<value>` and free-form notes.
- [ ] Implement team rules prompt with business-language wording.
- [ ] Implement per-candidate Guide/Sensor review with accept/reject/keep/edit-note.
- [ ] Implement workflow preview and confirmation recording.
- [ ] Implement final summary with `confirm`, `back`, and `cancel`.
- [ ] Apply primary stack override and scan notes to `ProjectInventory.stack_extensions`.
- [ ] Re-run targeted integration tests.

## Task 3: Asset Writer Consumption

- [ ] Write failing unit/integration assertions that scan correction notes and workflow confirmation appear in generated guide/human input material.
- [ ] Update guide generation to include human scan corrections and workflow confirmation.
- [ ] Ensure candidate review markdown includes edited decision notes via existing candidate report data.
- [ ] Run targeted tests.

## Task 4: Docs And Todo Closure

- [ ] Update README guided init section with the new Chinese UX.
- [ ] Mark `docs/todos/guided-init-human-centered-cli.md` implemented and describe the implementation result.
- [ ] Update `docs/todos/README.md` and archive if appropriate.
- [ ] Run `scripts/test-fast.sh`.

## Self-Review

Spec coverage:

- Chinese explanatory output: Task 2.
- Open supplement and scan correction: Task 2.
- Candidate one-by-one review: Task 2.
- Workflow preview: Task 2.
- Summary and backtracking: Task 2.
- Structured decisions and asset effects: Tasks 1-3.
- Non-interactive compatibility: Task 2 and full regression.

No placeholders are intentionally left in this plan; implementation details are constrained to existing modules and schema.
