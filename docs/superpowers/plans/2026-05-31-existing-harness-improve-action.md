# Existing Harness Improve Action Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an existing-Harness guided `init` action that generates maturity-driven review-only improvement candidates.

**Architecture:** Refresh Experience index, run `assess_maturity(repo)`, then run deterministic `generate_improvements(repo)` from `interactive_init.py`. The guided action records init trace events and artifacts, prints a concise Chinese action summary including the top candidate, and returns `.ai` so the existing CLI completion renderer can show the refreshed maturity summary.

**Tech Stack:** Python, Typer CLI, Pydantic schemas, pytest integration tests, Markdown docs.

---

## Files

- Modify `src/harness_builder_agent/tools/interactive_init.py`
  - Import `generate_improvements`, `write_experience_index`, and `ImprovementCandidateReport`.
  - Add `improve` menu copy and action branch.
  - Add a small helper for top candidate output.
  - Record trace artifacts for generated review-only outputs.
- Modify `tests/integration/test_init_on_fixture_projects.py`
  - Add a guided existing-Harness `improve` integration test.
- Modify `README.md`
  - Mention `improve` in existing Harness maintenance actions.
- Modify `docs/engineering/init-workflow.md`
  - Record the stable guided `improve` maintenance behavior.
- Modify `docs/todos/maturity-driven-init-wizard.md`
  - Add completed slice.
- Modify `docs/evolution-log.md`
  - Add concise evolution summary.

## Tasks

### Task 1: Add Failing Integration Test

- [ ] Add a test named `test_guided_init_existing_harness_can_improve_without_overwriting_formal_assets` in `tests/integration/test_init_on_fixture_projects.py`.
- [ ] Arrange a fixture Harness with `init --non-interactive`.
- [ ] Save `project-inventory.json`, `harness-config.yaml`, `.ai/guides/project-context.md`, `.ai/sensors/verification.md`, and `.ai/skills/lightweight/SKILL.md`.
- [ ] Patch `harness_builder_agent.tools.interactive_init.scan_repository` to raise.
- [ ] Run guided `init` with input `improve\n`.
- [ ] Assert the current implementation fails because the output does not contain `改进候选已生成`.
- [ ] Assert the future output includes `优先候选` and a candidate id from `improvement-candidates.yaml`.
- [ ] Add a second stale-evidence test that writes `.ai/review/workflow-routing-recommendation.yaml`, leaves Experience index stale, runs guided `init -> improve`, and asserts the workflow recommendation becomes maturity evidence and an improvement candidate.

Command:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_improve_without_overwriting_formal_assets -q
```

Expected before implementation:

```text
FAILED ... assert '改进候选已生成' in result.output
```

### Task 2: Implement Guided Improve Action

- [ ] Import `ImprovementCandidateReport`, `generate_improvements`, and `write_experience_index` in `src/harness_builder_agent/tools/interactive_init.py`.
- [ ] Add menu line:

```python
typer.echo("- improve：基于成熟度缺口生成 review-only 改进候选，不覆盖正式 Harness 资产。")
```

- [ ] Add action branch:

```python
if action in {"improve", "建议", "改进"}:
    typer.echo("正在生成成熟度驱动的改进候选...")
    trace.event(
        "existing-harness",
        "started",
        "Existing Harness detected; user chose improvement candidate generation.",
        {"primary_stack": inventory.primary_stack, "action": "improve"},
    )
    write_experience_index(ai)
    output_dir = assess_maturity(repo)
    output_dir = generate_improvements(repo)
    trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
    trace.artifact(output_dir / "maturity-report.md", "maturity_report")
    trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
    trace.artifact(output_dir / "init-summary.md", "init_summary")
    trace.artifact(output_dir / "improvement-candidates.yaml", "improvement_candidates")
    trace.artifact(output_dir / "evolution-plan.md", "plan")
    trace.artifact(output_dir / "experience" / "pending-improvements.md", "experience")
    trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
    trace.event(
        "existing-harness",
        "completed",
        "Existing Harness improvement candidates generated.",
        {"primary_stack": inventory.primary_stack, "action": "improve", "artifact_count": 8},
    )
    trace.finish(
        "completed",
        {
            "primary_stack": inventory.primary_stack,
            "existing_harness_action": "improve",
                "artifact_count": 8,
        },
    )
    typer.echo("改进候选已生成。")
    typer.echo(_top_improvement_candidate(output_dir / "improvement-candidates.yaml"))
    typer.echo("- `.ai/improvement-candidates.yaml`")
    typer.echo("- `.ai/evolution-plan.md`")
    typer.echo("- `.ai/experience/pending-improvements.md`")
    typer.echo("- `.ai/experience/experience-index.yaml`")
    return output_dir
```

- [ ] Add helper:

```python
def _top_improvement_candidate(path: Path) -> str:
    report = ImprovementCandidateReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    if not report.candidates:
        return "优先候选：暂无候选。"
    priority_order = {"high": 0, "medium": 1, "low": 2}
    candidate = sorted(report.candidates, key=lambda item: (priority_order.get(item.priority, 3), item.id))[0]
    return (
        f"优先候选：`{candidate.id}`"
        f"（priority={candidate.priority}，dimension={candidate.target_dimension or 'unknown'}，"
        f"target=`{candidate.suggested_target}`）"
    )
```

### Task 3: Verify Behavior and Docs

- [ ] Run the new integration test and confirm it passes.
- [ ] Run all init integration tests:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q
```

- [ ] Run improve-related integration tests:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_improve_generates_reviewable_improvement_candidates tests/integration/test_assess_improve_commands.py::test_improve_candidates_are_reviewable_and_target_ai_assets -q
```

- [ ] Update long-lived docs listed above.
- [ ] Run `scripts/test-fast.sh` before commit.
