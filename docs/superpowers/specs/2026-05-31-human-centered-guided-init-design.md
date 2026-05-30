# Human-Centered Guided Init Design

## Goal

Enhance `harness-builder-agent init` guided mode from a field-confirmation wizard into a Chinese, human-centered CLI flow where project maintainers can understand scan conclusions, add or correct information, review Guide/Sensor/Workflow recommendations, see a final summary, and return to key stages before writing `.ai` assets.

## Brainstorming Questions And Decisions

Because this work is running under goal mode, product questions are answered here instead of blocking for user confirmation.

- Should the CLI expose internal fields like `primary_stack`? No. Internal field names may appear in generated machine files, but the interactive UI should speak in Chinese concepts such as “主要技术栈”, “模块”, “验证命令”, “规则”, “传感器”.
- Should scan correction be fully natural-language parsed in the first implementation? No. First version should support reliable structured correction snippets for primary stack, modules, validation commands, and risk areas, while recording other free-form text as notes. It should not silently infer machine state from ambiguous prose.
- Should context be called `context` in the UI? No. Use “团队规则”, “架构规范”, “测试策略”, “安全合规要求” in prompts. `context` remains an internal artifact name.
- Should Guide/Sensor candidates be reviewed one by one? Yes. The UI should show each candidate title, purpose, evidence, and consequence of accept/reject/keep.
- Should candidate editing support full Markdown editing now? No. First version supports accept/reject/keep/edit-note. Edit-note is reflected in candidate status notes and generated review material; full content editing can come later.
- Should Workflow be editable now? No. First version explains the configured workflows and records that they were shown. The default workflow config remains deterministic.
- How much backtracking is required now? At least final-summary backtracking to scan/context/candidate review. Full per-step `back` everywhere can be added later.
- Should this require a new terminal UI library? No. Keep dependencies unchanged and use Typer prompts plus clear sectioned text. This avoids introducing unneeded dependency risk.

## User Experience

The guided flow is:

1. Show a short welcome with the target repository and explain that the tool will generate editable `.ai` Harness assets.
2. Scan the repository.
3. Present “扫描发现” in Chinese:
   - human-readable primary stack label and explanation;
   - evidence list from project inventory and scan metadata;
   - modules;
   - command candidates;
   - scan warnings.
4. Ask for open supplement:
   - empty input means continue;
   - `stack=<value>` or choosing from a stack correction prompt updates the primary stack override;
   - any other text is recorded as scan correction notes and later appears in generated guides/human input.
5. Ask for team rules using business language:
   - code conventions;
   - architecture constraints;
   - testing strategy;
   - safety/compliance/release requirements;
   - directories or modules that should not be changed casually.
6. Show Guide candidates one by one:
   - built-in guide weapons;
   - LLM guide candidates.
   Each item displays title, purpose, source/evidence, and the effect of accepting/rejecting/keeping.
7. Show Sensor candidates one by one:
   - built-in sensor weapons;
   - command catalog hard/soft gates;
   - LLM sensor candidates.
   Each item explains what it validates, whether it is already discovered or a missing capability, and the gate implication.
8. Show Workflow suggestions:
   - `lightweight` for low-risk small changes;
   - `bugfix` for defect repair with root cause investigation and sensor checks.
9. Show final summary:
   - stack, modules, team rule count, Guide decisions, Sensor decisions, workflows, files to write, unresolved follow-ups.
   User can type `confirm`, `back`, or `cancel`.
10. If `back`, prompt for a stage: `scan`, `rules`, or `candidates`, then rerun that stage and show the summary again.
11. On `confirm`, write `.ai` assets and record interaction decisions.

## Data Model

Extend `InteractionDecisions` conservatively:

- `ScanConfirmation.notes` already records scan correction text.
- `ScanConfirmation.primary_stack_override` already records primary stack override.
- Structured scan snippets update `ProjectInventory.modules`, `CommandCatalog.commands`, and `stack_extensions["risk_areas"]`, and are also copied to `stack_extensions["human_overrides"]`.
- Add `workflow_confirmation` to record shown/confirmed workflows and notes.
- Extend `CandidateDecision.decision` to include `edited` for “keep as candidate but with user notes”.

Do not add broad ad hoc dicts. Any new machine-consumed field must be in Pydantic schema.

## Asset Effects

User input must not only appear in terminal output.

- Primary stack override updates `ProjectInventory.primary_stack`, selected stack list, and `stack_extensions["human_overrides"]`.
- Free-form scan notes enter `stack_extensions["human_overrides"]["scan_notes"]`.
- Team rules enter `interaction-decisions.yaml`, `human-input-needed.md`, and generated guides.
- Candidate decisions affect `weapon-library-candidates.yaml` status via existing candidate decision application.
- Candidate notes appear in candidate review markdown.
- Workflow confirmation appears in `interaction-decisions.yaml` and final decision log.

## Non-Interactive Mode

`--non-interactive` remains compatible:

- no prompts;
- no blocking;
- candidates remain candidate;
- final confirmation remains `not_confirmed`;
- generated questionnaire/human-input files continue to expose required human confirmation.

## Error Handling

- `cancel` aborts before writing and records failed/cancelled trace.
- Invalid stack correction prompts again with allowed values.
- Unknown final summary command explains valid commands instead of writing files.
- Candidate decisions accept only `a`, `r`, `k`, `e`, or empty/default keep.

## Testing

Tests must cover:

- guided happy path uses Chinese explanatory section labels and no longer relies on `primary_stack` UI text;
- scan supplement notes are recorded and visible in generated guides;
- stack correction affects `project-inventory.json` and interaction decisions;
- Guide/Sensor candidates are shown individually and decisions update candidate status;
- Workflow suggestions are displayed and recorded;
- final summary supports `back` to rules or candidates before confirm;
- non-interactive mode still passes existing tests.

## Scope Limits

This design intentionally does not implement full natural-language parsing, rich terminal components, full Markdown candidate editing, or a separate `confirm` command. It creates a better local guided `init` experience while preserving the current deterministic generation architecture.
