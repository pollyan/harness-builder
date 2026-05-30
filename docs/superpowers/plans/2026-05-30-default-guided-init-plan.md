# Default Guided Init Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `harness-builder-agent init` default to a guided human-in-the-loop workflow while preserving explicit `--non-interactive` automation for tests, CI, scripts, and acceptance.

**Architecture:** Add a structured interaction decision schema, route `init` through a thin orchestration layer, and keep CLI business logic minimal. Non-interactive mode records explicit unconfirmed decisions; interactive mode collects confirmations through Typer prompts and writes the same machine-readable contract into `.ai/interaction-decisions.yaml`, trace artifacts, human confirmation assets, and candidate review assets.

**Tech Stack:** Python 3.11+, Typer, Pydantic, PyYAML, pytest, Typer `CliRunner`.

---

## File Structure

Create:

- `src/harness_builder_agent/schemas/interaction_decision.py`: Pydantic contract for `.ai/interaction-decisions.yaml`.
- `src/harness_builder_agent/tools/interaction_decisions.py`: builders, candidate decision application, Markdown summary.
- `src/harness_builder_agent/tools/interactive_init.py`: `init` orchestration for interactive and non-interactive modes.
- `tests/unit/test_interaction_decisions.py`: schema and transformation tests.

Modify:

- `src/harness_builder_agent/cli.py`: add `--non-interactive`; default TTY runs guided mode; non-TTY without flag fails.
- `src/harness_builder_agent/tools/write_assets.py`: accept optional interaction decisions and pass them to writers.
- `src/harness_builder_agent/tools/asset_writers/human_confirmation.py`: write `interaction-decisions.yaml` and include decisions in human input.
- `src/harness_builder_agent/tools/asset_writers/candidates.py`: write candidate statuses after decisions are applied.
- `src/harness_builder_agent/tools/asset_writers/guides.py`: include confirmed context summaries in project context guide.
- `src/harness_builder_agent/tools/human_confirmation.py`: extend context input records with confirmation status and inline contexts.
- `tests/integration/test_init_on_fixture_projects.py`: update existing tests to use `--non-interactive`, add default interactive happy path and non-TTY failure.
- `tests/acceptance/test_real_repositories_e2e.py`: pass `--non-interactive` to `init`.
- `docs/todos/interactive-guided-cli.md`: mark implemented after verification.
- `README.md`, `docs/engineering/init-workflow.md`, `docs/engineering/testing-strategy.md`: document default guided mode and explicit automation mode.

Do not change:

- `run`, `assess`, `improve`, or `benchmark` behavior in this task.
- DeepSeek fallback rules.
- Workflow skill template generation.

---

### Task 1: Interaction Decision Schema

**Files:**
- Create: `src/harness_builder_agent/schemas/interaction_decision.py`
- Create: `tests/unit/test_interaction_decisions.py`

- [ ] **Step 1: Write failing schema tests**

Create `tests/unit/test_interaction_decisions.py`:

```python
from __future__ import annotations

import pytest
from pydantic import ValidationError

from harness_builder_agent.schemas.interaction_decision import (
    CandidateDecision,
    ContextConfirmation,
    FinalConfirmation,
    InteractionDecisions,
    RepoConfirmation,
    ScanConfirmation,
)


def test_interaction_decisions_schema_accepts_interactive_confirmation():
    decisions = InteractionDecisions(
        mode="interactive",
        repo=RepoConfirmation(path="/repo", confirmed=True),
        scan_confirmation=ScanConfirmation(status="accepted", notes=["确认 Java Spring 判断"]),
        context_confirmation=ContextConfirmation(
            status="confirmed",
            confirmed_paths=["/repo/team-rules.md"],
            inline_contexts=["所有 Controller 只能调用 Service"],
        ),
        candidate_decisions=[
            CandidateDecision(candidate_id="llm-guide-risk-001", decision="accepted", notes="团队认可")
        ],
        final_confirmation=FinalConfirmation(status="confirmed"),
    )

    payload = decisions.model_dump(mode="json")

    assert payload["schema_version"] == "1.0"
    assert payload["mode"] == "interactive"
    assert payload["repo"]["confirmed"] is True
    assert payload["candidate_decisions"][0]["decision"] == "accepted"


def test_interaction_decisions_schema_rejects_invalid_candidate_decision():
    with pytest.raises(ValidationError):
        CandidateDecision(candidate_id="candidate-1", decision="promote")
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_interaction_decisions.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'harness_builder_agent.schemas.interaction_decision'`.

- [ ] **Step 3: Implement schema**

Create `src/harness_builder_agent/schemas/interaction_decision.py`:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


InteractionMode = Literal["interactive", "non_interactive"]
ScanConfirmationStatus = Literal["accepted", "amended", "needs_review", "not_confirmed"]
ContextConfirmationStatus = Literal["confirmed", "partially_confirmed", "not_provided", "not_confirmed"]
CandidateDecisionStatus = Literal["accepted", "rejected", "kept"]
FinalConfirmationStatus = Literal["confirmed", "cancelled", "not_confirmed"]


class RepoConfirmation(BaseModel):
    path: str
    confirmed: bool = False


class ScanConfirmation(BaseModel):
    status: ScanConfirmationStatus = "not_confirmed"
    primary_stack_override: str | None = None
    notes: list[str] = Field(default_factory=list)


class ContextConfirmation(BaseModel):
    status: ContextConfirmationStatus = "not_provided"
    confirmed_paths: list[str] = Field(default_factory=list)
    rejected_paths: list[str] = Field(default_factory=list)
    inline_contexts: list[str] = Field(default_factory=list)


class CandidateDecision(BaseModel):
    candidate_id: str
    decision: CandidateDecisionStatus = "kept"
    notes: str = ""


class FinalConfirmation(BaseModel):
    status: FinalConfirmationStatus = "not_confirmed"


class InteractionDecisions(BaseModel):
    schema_version: str = "1.0"
    mode: InteractionMode
    repo: RepoConfirmation
    scan_confirmation: ScanConfirmation = Field(default_factory=ScanConfirmation)
    context_confirmation: ContextConfirmation = Field(default_factory=ContextConfirmation)
    candidate_decisions: list[CandidateDecision] = Field(default_factory=list)
    final_confirmation: FinalConfirmation = Field(default_factory=FinalConfirmation)
```

- [ ] **Step 4: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_interaction_decisions.py -q
scripts/test-fast.sh
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/harness_builder_agent/schemas/interaction_decision.py tests/unit/test_interaction_decisions.py
git commit -m "feat: add interaction decision schema"
```

---

### Task 2: Decision Builders and Candidate Status Application

**Files:**
- Create: `src/harness_builder_agent/tools/interaction_decisions.py`
- Modify: `tests/unit/test_interaction_decisions.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/unit/test_interaction_decisions.py`:

```python
from harness_builder_agent.tools.interaction_decisions import (
    apply_candidate_decisions,
    default_non_interactive_decisions,
    interaction_decisions_markdown,
)


def test_default_non_interactive_decisions_record_missing_human_confirmation():
    decisions = default_non_interactive_decisions("/repo", context_paths=["/repo/team-rules.md"])

    assert decisions.mode == "non_interactive"
    assert decisions.repo.confirmed is False
    assert decisions.scan_confirmation.status == "not_confirmed"
    assert decisions.context_confirmation.status == "not_confirmed"
    assert decisions.context_confirmation.confirmed_paths == []
    assert decisions.final_confirmation.status == "not_confirmed"


def test_apply_candidate_decisions_updates_statuses_and_reasons():
    report = {
        "schema_version": "1.0",
        "source": "llm_scan_proposal",
        "candidates": [
            {"id": "llm-guide-risk-001", "status": "candidate", "human_confirmation_required": True},
            {"id": "llm-sensor-command-001", "status": "candidate", "human_confirmation_required": True},
            {"id": "llm-guide-keep-001", "status": "candidate", "human_confirmation_required": True},
        ],
    }
    decisions = InteractionDecisions(
        mode="interactive",
        repo=RepoConfirmation(path="/repo", confirmed=True),
        candidate_decisions=[
            CandidateDecision(candidate_id="llm-guide-risk-001", decision="accepted", notes="认可"),
            CandidateDecision(candidate_id="llm-sensor-command-001", decision="rejected", notes="命令不稳定"),
        ],
    )

    updated = apply_candidate_decisions(report, decisions)
    by_id = {item["id"]: item for item in updated["candidates"]}

    assert by_id["llm-guide-risk-001"]["status"] == "confirmed"
    assert by_id["llm-guide-risk-001"]["human_confirmation_required"] is False
    assert by_id["llm-guide-risk-001"]["decision_notes"] == "认可"
    assert by_id["llm-sensor-command-001"]["status"] == "rejected"
    assert by_id["llm-sensor-command-001"]["decision_notes"] == "命令不稳定"
    assert by_id["llm-guide-keep-001"]["status"] == "candidate"


def test_interaction_decisions_markdown_summarizes_decisions():
    decisions = InteractionDecisions(
        mode="interactive",
        repo=RepoConfirmation(path="/repo", confirmed=True),
        scan_confirmation=ScanConfirmation(status="accepted"),
        context_confirmation=ContextConfirmation(status="confirmed", inline_contexts=["团队测试策略"]),
        final_confirmation=FinalConfirmation(status="confirmed"),
    )

    markdown = interaction_decisions_markdown(decisions)

    assert "# Interaction Decisions" in markdown
    assert "mode: interactive" in markdown
    assert "scan: accepted" in markdown
    assert "团队测试策略" in markdown
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_interaction_decisions.py -q
```

Expected: FAIL because `harness_builder_agent.tools.interaction_decisions` does not exist.

- [ ] **Step 3: Implement decision helpers**

Create `src/harness_builder_agent/tools/interaction_decisions.py`:

```python
from __future__ import annotations

from copy import deepcopy

from harness_builder_agent.schemas.interaction_decision import (
    CandidateDecision,
    ContextConfirmation,
    FinalConfirmation,
    InteractionDecisions,
    RepoConfirmation,
    ScanConfirmation,
)


def default_non_interactive_decisions(repo_path: str, context_paths: list[str] | None = None) -> InteractionDecisions:
    status = "not_confirmed" if context_paths else "not_provided"
    return InteractionDecisions(
        mode="non_interactive",
        repo=RepoConfirmation(path=repo_path, confirmed=False),
        scan_confirmation=ScanConfirmation(status="not_confirmed"),
        context_confirmation=ContextConfirmation(status=status),
        candidate_decisions=[],
        final_confirmation=FinalConfirmation(status="not_confirmed"),
    )


def accepted_interactive_decisions(
    repo_path: str,
    *,
    context_paths: list[str] | None = None,
    inline_contexts: list[str] | None = None,
    candidate_ids: list[str] | None = None,
    accept_candidates: bool = False,
) -> InteractionDecisions:
    confirmed_paths = context_paths or []
    inline_values = [item for item in (inline_contexts or []) if item.strip()]
    if confirmed_paths or inline_values:
        context_status = "confirmed"
    else:
        context_status = "not_provided"
    candidate_decisions = [
        CandidateDecision(candidate_id=candidate_id, decision="accepted" if accept_candidates else "kept")
        for candidate_id in (candidate_ids or [])
    ]
    return InteractionDecisions(
        mode="interactive",
        repo=RepoConfirmation(path=repo_path, confirmed=True),
        scan_confirmation=ScanConfirmation(status="accepted"),
        context_confirmation=ContextConfirmation(
            status=context_status,
            confirmed_paths=confirmed_paths,
            inline_contexts=inline_values,
        ),
        candidate_decisions=candidate_decisions,
        final_confirmation=FinalConfirmation(status="confirmed"),
    )


def apply_candidate_decisions(report: dict, decisions: InteractionDecisions) -> dict:
    updated = deepcopy(report)
    by_id = {item.candidate_id: item for item in decisions.candidate_decisions}
    for candidate in updated.get("candidates", []):
        decision = by_id.get(candidate.get("id"))
        if not decision:
            continue
        candidate["decision_notes"] = decision.notes
        if decision.decision == "accepted":
            candidate["status"] = "confirmed"
            candidate["human_confirmation_required"] = False
        elif decision.decision == "rejected":
            candidate["status"] = "rejected"
            candidate["human_confirmation_required"] = False
        else:
            candidate["status"] = "candidate"
            candidate["human_confirmation_required"] = True
    return updated


def interaction_decisions_markdown(decisions: InteractionDecisions) -> str:
    context_lines = decisions.context_confirmation.inline_contexts or ["无"]
    candidate_lines = [
        f"- `{item.candidate_id}`: {item.decision} {item.notes}".rstrip()
        for item in decisions.candidate_decisions
    ] or ["- 无逐项 candidate 决策。"]
    return (
        "# Interaction Decisions\n\n"
        f"- mode: {decisions.mode}\n"
        f"- repo_confirmed: {decisions.repo.confirmed}\n"
        f"- scan: {decisions.scan_confirmation.status}\n"
        f"- context: {decisions.context_confirmation.status}\n"
        f"- final: {decisions.final_confirmation.status}\n\n"
        "## Inline Context\n\n"
        + "\n".join(f"- {item}" for item in context_lines)
        + "\n\n## Candidate Decisions\n\n"
        + "\n".join(candidate_lines)
        + "\n"
    )
```

- [ ] **Step 4: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_interaction_decisions.py -q
scripts/test-fast.sh
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/harness_builder_agent/tools/interaction_decisions.py tests/unit/test_interaction_decisions.py
git commit -m "feat: build interaction decisions"
```

---

### Task 3: Write Interaction Decisions With Init Assets

**Files:**
- Modify: `src/harness_builder_agent/tools/write_assets.py`
- Modify: `src/harness_builder_agent/tools/asset_writers/human_confirmation.py`
- Modify: `src/harness_builder_agent/tools/asset_writers/candidates.py`
- Modify: `src/harness_builder_agent/tools/human_confirmation.py`
- Modify: `tests/unit/test_write_assets.py`
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [ ] **Step 1: Write failing tests**

In `tests/unit/test_write_assets.py`, extend imports:

```python
from harness_builder_agent.tools.interaction_decisions import accepted_interactive_decisions
```

Add this test:

```python
def test_write_initial_assets_persists_interaction_decisions_and_applies_candidate_status(tmp_path: Path):
    context = tmp_path / "team-rules.md"
    context.write_text("团队规则：Controller 只能调用 Service。", encoding="utf-8")
    trace = GenerationTrace.start(tmp_path, "init")
    decisions = accepted_interactive_decisions(
        str(tmp_path),
        context_paths=[str(context)],
        inline_contexts=["所有新增逻辑必须有测试"],
        candidate_ids=["llm-guide-architecture-001"],
        accept_candidates=True,
    )

    ai = write_initial_assets(
        tmp_path,
        _inventory(tmp_path),
        _commands(),
        trace=trace,
        context_paths=[context],
        interaction_decisions=decisions,
    )

    decision_payload = yaml.safe_load((ai / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decision_payload["mode"] == "interactive"
    assert decision_payload["final_confirmation"]["status"] == "confirmed"
    human_input = (ai / "human-input-needed.md").read_text(encoding="utf-8")
    assert "Interaction Decisions" in human_input
    assert "所有新增逻辑必须有测试" in human_input
    candidates = yaml.safe_load((ai / "experience" / "weapon-library-candidates.yaml").read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in candidates["candidates"]}
    assert by_id["llm-guide-architecture-001"]["status"] == "confirmed"
    assert by_id["llm-guide-architecture-001"]["human_confirmation_required"] is False
```

In `tests/integration/test_init_on_fixture_projects.py`, inside `_assert_init_outputs`, add:

```python
    assert (ai / "interaction-decisions.yaml").exists()
    interaction_decisions = yaml.safe_load((ai / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert interaction_decisions["schema_version"] == "1.0"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_write_assets.py::test_write_initial_assets_persists_interaction_decisions_and_applies_candidate_status -q
```

Expected: FAIL because `write_initial_assets()` does not accept `interaction_decisions`.

- [ ] **Step 3: Update writers**

Modify `src/harness_builder_agent/tools/write_assets.py` imports:

```python
from harness_builder_agent.schemas.interaction_decision import InteractionDecisions
from harness_builder_agent.tools.interaction_decisions import apply_candidate_decisions, default_non_interactive_decisions
```

Change signature:

```python
def write_initial_assets(
    repo: Path,
    inventory: ProjectInventory,
    commands: CommandCatalog,
    trace: GenerationTrace | None = None,
    context_paths: list[Path] | None = None,
    interaction_decisions: InteractionDecisions | None = None,
) -> Path:
```

After `context_inputs = read_context_inputs(context_paths or [])`, add:

```python
    decisions = interaction_decisions or default_non_interactive_decisions(
        str(repo),
        context_paths=[str(path) for path in (context_paths or [])],
    )
```

Replace:

```python
    enhancement_candidates = build_llm_enhancement_candidates(inventory, commands)
```

with:

```python
    enhancement_candidates = apply_candidate_decisions(build_llm_enhancement_candidates(inventory, commands), decisions)
```

Replace:

```python
    write_human_confirmation_assets(ai, context_inputs, questionnaire, trace=trace)
```

with:

```python
    write_human_confirmation_assets(ai, context_inputs, questionnaire, decisions, trace=trace)
```

Modify `src/harness_builder_agent/tools/asset_writers/human_confirmation.py`:

```python
from harness_builder_agent.schemas.interaction_decision import InteractionDecisions
from harness_builder_agent.tools.interaction_decisions import interaction_decisions_markdown
```

Change signature:

```python
def write_human_confirmation_assets(
    ai: Path,
    context_inputs: dict[str, Any],
    questionnaire: dict[str, Any],
    interaction_decisions: InteractionDecisions,
    trace: GenerationTrace | None = None,
) -> None:
```

After questionnaire write:

```python
    write_yaml(ai / "interaction-decisions.yaml", interaction_decisions.model_dump(mode="json"))
    record_artifact(trace, ai / "interaction-decisions.yaml", "interaction_decisions")
```

Replace human input write:

```python
    write_text(
        ai / "human-input-needed.md",
        human_input_markdown(context_inputs, questionnaire, interaction_decisions_markdown(interaction_decisions)),
    )
```

Modify `src/harness_builder_agent/tools/human_confirmation.py` signature:

```python
def human_input_markdown(context_inputs: dict[str, Any], questionnaire: dict[str, Any], decision_markdown: str = "") -> str:
```

Append the decision section before next steps:

```python
        + ("\n\n" + decision_markdown if decision_markdown else "")
        + "\n\n## 下一步建议\n\n"
```

- [ ] **Step 4: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_write_assets.py tests/integration/test_init_on_fixture_projects.py -q
scripts/test-fast.sh
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/harness_builder_agent/tools/write_assets.py src/harness_builder_agent/tools/asset_writers/human_confirmation.py src/harness_builder_agent/tools/human_confirmation.py tests/unit/test_write_assets.py tests/integration/test_init_on_fixture_projects.py
git commit -m "feat: write interaction decisions"
```

---

### Task 4: Non-Interactive Init Mode and Non-TTY Default Failure

**Files:**
- Modify: `src/harness_builder_agent/cli.py`
- Create: `src/harness_builder_agent/tools/interactive_init.py`
- Modify: `tests/integration/test_init_on_fixture_projects.py`
- Modify: `tests/acceptance/test_real_repositories_e2e.py`

- [ ] **Step 1: Write failing integration tests**

In `tests/integration/test_init_on_fixture_projects.py`, add:

```python
def test_init_non_tty_requires_explicit_non_interactive(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="")

    assert result.exit_code != 0
    assert "--non-interactive" in result.output
    assert not (repo / ".ai" / "project-inventory.json").exists()


def test_init_non_interactive_generates_existing_assets(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])

    assert result.exit_code == 0, result.output
    _assert_init_outputs(repo, "java-spring")
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["mode"] == "non_interactive"
    assert decisions["final_confirmation"]["status"] == "not_confirmed"
```

Update existing non-interactive tests in this file:

```python
result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--context", str(context), "--non-interactive"])
result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
result = CliRunner().invoke(app, ["init", "--non-interactive"])
```

In `tests/acceptance/test_real_repositories_e2e.py`, change:

```python
init_result = _run_cli("init", "--repo", str(repo))
```

to:

```python
init_result = _run_cli("init", "--repo", str(repo), "--non-interactive")
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_non_tty_requires_explicit_non_interactive tests/integration/test_init_on_fixture_projects.py::test_init_non_interactive_generates_existing_assets -q
```

Expected: FAIL because `--non-interactive` is not recognized and default non-TTY still generates assets.

- [ ] **Step 3: Implement non-interactive orchestration**

Create `src/harness_builder_agent/tools/interactive_init.py`:

```python
from __future__ import annotations

from pathlib import Path

from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.interaction_decisions import default_non_interactive_decisions
from harness_builder_agent.tools.scan_repo import scan_repository
from harness_builder_agent.tools.write_assets import write_initial_assets


def run_non_interactive_init(repo: Path, context_paths: list[Path], trace: GenerationTrace) -> Path:
    trace.event("scan", "started", "Repository scan started.")
    inventory, commands = scan_repository(repo)
    trace.event(
        "scan",
        "completed",
        "Repository scan completed.",
        {"primary_stack": inventory.primary_stack, "stacks": inventory.stacks, "command_count": len(commands.commands)},
    )
    decisions = default_non_interactive_decisions(str(repo), context_paths=[str(path) for path in context_paths])
    output_dir = write_initial_assets(
        repo,
        inventory,
        commands,
        trace=trace,
        context_paths=context_paths,
        interaction_decisions=decisions,
    )
    trace.finish("completed", {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)})
    return output_dir
```

Modify `src/harness_builder_agent/cli.py` imports:

```python
from harness_builder_agent.tools.interactive_init import run_non_interactive_init
```

Add parameter:

```python
    non_interactive: bool = typer.Option(False, "--non-interactive", help="Run init without prompts for CI, scripts, and acceptance."),
```

At the start of `init_command`, after repo validation:

```python
    if not non_interactive:
        raise typer.BadParameter("`init` now defaults to guided interactive mode. Non-TTY automation must pass --non-interactive.")
```

Replace the try body with:

```python
        output_dir = run_non_interactive_init(target_repo, context or [], trace)
```

Keep exception handling and echo unchanged.

This step intentionally makes all non-interactive callers explicit before implementing guided TTY prompts.

- [ ] **Step 4: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q
scripts/test-fast.sh
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/harness_builder_agent/cli.py src/harness_builder_agent/tools/interactive_init.py tests/integration/test_init_on_fixture_projects.py tests/acceptance/test_real_repositories_e2e.py
git commit -m "feat: require explicit non-interactive init"
```

---

### Task 5: Guided Interactive Init Happy Path

**Files:**
- Modify: `src/harness_builder_agent/tools/interactive_init.py`
- Modify: `src/harness_builder_agent/cli.py`
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [ ] **Step 1: Write failing interactive happy path test**

In `tests/integration/test_init_on_fixture_projects.py`, add:

```python
def test_init_default_guided_mode_accepts_happy_path(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input="\n\nn\nk\n\n",
    )

    assert result.exit_code == 0, result.output
    assert "扫描结论" in result.output
    assert "候选 Guide/Sensor" in result.output
    _assert_init_outputs(repo, "java-spring")
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["mode"] == "interactive"
    assert decisions["repo"]["confirmed"] is True
    assert decisions["scan_confirmation"]["status"] == "accepted"
    assert decisions["final_confirmation"]["status"] == "confirmed"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path -q
```

Expected: FAIL because default mode still raises the `--non-interactive` error.

- [ ] **Step 3: Implement guided happy path**

Modify `src/harness_builder_agent/tools/interactive_init.py` imports:

```python
import typer
from harness_builder_agent.tools.interaction_decisions import accepted_interactive_decisions
from harness_builder_agent.tools.llm_enhancement_candidates import build_llm_enhancement_candidates
```

Add:

```python
def run_guided_init(repo: Path, context_paths: list[Path], trace: GenerationTrace) -> Path:
    typer.echo(f"仓库: {repo}")
    if not typer.confirm("继续生成 Harness?", default=True):
        trace.finish("failed", {"cancelled": True})
        raise typer.Abort()

    trace.event("scan", "started", "Repository scan started.")
    inventory, commands = scan_repository(repo)
    trace.event(
        "scan",
        "completed",
        "Repository scan completed.",
        {"primary_stack": inventory.primary_stack, "stacks": inventory.stacks, "command_count": len(commands.commands)},
    )

    typer.echo("扫描结论")
    typer.echo(f"- primary_stack: {inventory.primary_stack}")
    typer.echo(f"- stacks: {', '.join(inventory.stacks)}")
    typer.echo(f"- commands: {len(commands.commands)}")
    if not typer.confirm("接受扫描结论?", default=True):
        trace.finish("failed", {"cancelled": True})
        raise typer.Abort()

    inline_contexts: list[str] = []
    if typer.confirm("是否补充团队 context?", default=False):
        inline = typer.prompt("请输入团队 context 摘要", default="")
        if inline.strip():
            inline_contexts.append(inline.strip())

    candidate_report = build_llm_enhancement_candidates(inventory, commands)
    candidate_ids = [item["id"] for item in candidate_report.get("candidates", [])]
    typer.echo(f"候选 Guide/Sensor: {len(candidate_ids)}")
    candidate_choice = typer.prompt("候选处理方式: a=全部接受, k=保持候选", default="k").strip().lower()
    accept_candidates = candidate_choice == "a"

    if not typer.confirm("确认写入 Harness 资产?", default=True):
        trace.finish("failed", {"cancelled": True})
        raise typer.Abort()

    decisions = accepted_interactive_decisions(
        str(repo),
        context_paths=[str(path) for path in context_paths],
        inline_contexts=inline_contexts,
        candidate_ids=candidate_ids,
        accept_candidates=accept_candidates,
    )
    output_dir = write_initial_assets(
        repo,
        inventory,
        commands,
        trace=trace,
        context_paths=context_paths,
        interaction_decisions=decisions,
    )
    trace.finish("completed", {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)})
    return output_dir
```

Modify `src/harness_builder_agent/cli.py` import:

```python
from harness_builder_agent.tools.interactive_init import run_guided_init, run_non_interactive_init
```

Replace non-interactive guard:

```python
    if not non_interactive and not typer.get_text_stream("stdin").isatty():
        raise typer.BadParameter("`init` defaults to guided interactive mode. Non-TTY automation must pass --non-interactive.")
```

Replace try body:

```python
        if non_interactive:
            output_dir = run_non_interactive_init(target_repo, context or [], trace)
        else:
            output_dir = run_guided_init(target_repo, context or [], trace)
```

- [ ] **Step 4: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q
scripts/test-fast.sh
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/harness_builder_agent/tools/interactive_init.py src/harness_builder_agent/cli.py tests/integration/test_init_on_fixture_projects.py
git commit -m "feat: add guided init happy path"
```

---

### Task 6: Context Participation in Guides

**Files:**
- Modify: `src/harness_builder_agent/tools/human_confirmation.py`
- Modify: `src/harness_builder_agent/tools/asset_writers/guides.py`
- Modify: `src/harness_builder_agent/tools/write_assets.py`
- Modify: `tests/unit/test_write_assets.py`
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [ ] **Step 1: Write failing tests**

In `tests/unit/test_write_assets.py`, add assertions to the interaction decision test:

```python
    project_context = (ai / "guides" / "project-context.md").read_text(encoding="utf-8")
    assert "## 团队上下文" in project_context
    assert "Controller 只能调用 Service" in project_context
    assert "所有新增逻辑必须有测试" in project_context
```

In `tests/integration/test_init_on_fixture_projects.py`, inside `test_init_generates_ai_assets_for_java_fixture`, after `_assert_init_outputs`:

```python
    project_context = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    assert "## 团队上下文" in project_context
    assert "Controller 只能调用 Service" in project_context
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_write_assets.py::test_write_initial_assets_persists_interaction_decisions_and_applies_candidate_status tests/integration/test_init_on_fixture_projects.py::test_init_generates_ai_assets_for_java_fixture -q
```

Expected: FAIL because project-context guide does not include team context.

- [ ] **Step 3: Pass context to guide writer**

Modify `src/harness_builder_agent/tools/asset_writers/guides.py` signature:

```python
def write_guide_assets(
    ai: Path,
    inventory: ProjectInventory,
    weapon_selection: WeaponLibrarySelection,
    context_inputs: dict[str, Any] | None = None,
    interaction_decisions: InteractionDecisions | None = None,
    trace: GenerationTrace | None = None,
) -> None:
```

Import:

```python
from typing import Any
from harness_builder_agent.schemas.interaction_decision import InteractionDecisions
```

Change project context write:

```python
    write_text(
        ai / "guides" / "project-context.md",
        _guide("project-context", inventory, weapon_selection, context_inputs, interaction_decisions),
    )
```

Change `_guide` signature:

```python
def _guide(
    name: str,
    inventory: ProjectInventory,
    weapon_selection: WeaponLibrarySelection,
    context_inputs: dict[str, Any] | None = None,
    interaction_decisions: InteractionDecisions | None = None,
) -> str:
```

Add helper:

```python
def _team_context_section(context_inputs: dict[str, Any] | None, interaction_decisions: InteractionDecisions | None) -> str:
    lines: list[str] = []
    for item in (context_inputs or {}).get("contexts", []):
        lines.append(f"- `{item['path']}`: {item['summary']}")
    if interaction_decisions:
        for item in interaction_decisions.context_confirmation.inline_contexts:
            lines.append(f"- {item}")
    return "\n".join(lines) or "- 暂未提供团队上下文。"
```

Inside `_guide`, before `## 当前项目事实`, include:

```python
        "## 团队上下文\n\n"
        f"{_team_context_section(context_inputs, interaction_decisions)}\n\n"
```

Modify `src/harness_builder_agent/tools/write_assets.py` call:

```python
    write_guide_assets(ai, inventory, weapon_selection, context_inputs, decisions, trace=trace)
```

- [ ] **Step 4: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_write_assets.py tests/integration/test_init_on_fixture_projects.py -q
scripts/test-fast.sh
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/harness_builder_agent/tools/asset_writers/guides.py src/harness_builder_agent/tools/write_assets.py tests/unit/test_write_assets.py tests/integration/test_init_on_fixture_projects.py
git commit -m "feat: include team context in guides"
```

---

### Task 7: Trace, Documentation, Todo Status, and Verification

**Files:**
- Modify: `src/harness_builder_agent/tools/generation_trace.py`
- Modify: `src/harness_builder_agent/tools/interactive_init.py`
- Modify: `src/harness_builder_agent/tools/asset_writers/human_confirmation.py`
- Modify: `README.md`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/engineering/testing-strategy.md`
- Modify: `docs/todos/interactive-guided-cli.md`

- [ ] **Step 1: Write failing trace assertion**

In `tests/integration/test_init_on_fixture_projects.py`, inside `_assert_init_outputs`, add:

```python
    assert ".ai/interaction-decisions.yaml" in artifact_paths
    decision_log = (latest / "decision-log.md").read_text(encoding="utf-8")
    assert "Interaction Decisions" in decision_log
```

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_non_interactive_generates_existing_assets -q
```

Expected: FAIL if decision log does not include interaction decisions.

- [ ] **Step 2: Record interaction decisions in trace decision log**

Modify `src/harness_builder_agent/tools/generation_trace.py`.

Add field to `GenerationTrace`:

```python
    decisions: list[dict[str, Any]] = field(default_factory=list)
```

Add method:

```python
    def decision(self, decision_id: str, message: str, details: dict[str, Any] | None = None) -> None:
        self.decisions.append(
            {
                "decision_id": decision_id,
                "message": message,
                "details": details or {},
            }
        )
```

In `_decision_log`, add:

```python
        decision_lines = "\n".join(
            f"- `{item['decision_id']}`: {item['message']}"
            for item in self.decisions
        ) or "- No structured decisions recorded."
```

Add this section before `## Artifacts`:

```python
            "## Interaction Decisions\n\n"
            f"{decision_lines}\n\n"
```

Modify `src/harness_builder_agent/tools/asset_writers/human_confirmation.py` after writing `interaction-decisions.yaml`:

```python
    if trace:
        trace.decision(
            "interaction-decisions",
            "Human interaction decisions recorded.",
            interaction_decisions.model_dump(mode="json"),
        )
```

- [ ] **Step 3: Update docs**

In `README.md`, document:

```markdown
默认本地向导：

```bash
.venv/bin/harness-builder-agent init
```

自动化或验收：

```bash
.venv/bin/harness-builder-agent init --non-interactive --repo .benchmarks/RuoYi-Vue
```
```

In `docs/engineering/init-workflow.md`, update inputs and failure behavior:

- `init` 默认交互式。
- `--non-interactive` 用于 CI、脚本、acceptance。
- 非 TTY 未传 `--non-interactive` 必须失败。
- `.ai/interaction-decisions.yaml` 是必须生成的机器消费产物。

In `docs/engineering/testing-strategy.md`, update init coverage:

- 默认 guided mode happy path。
- non-TTY without `--non-interactive` failure.
- `--non-interactive` compatibility.

In `docs/todos/interactive-guided-cli.md`, change:

```markdown
- 状态：implemented
```

Append implementation results:

```markdown
## 实现结果

- `init` 默认进入 guided interactive mode。
- 自动化场景使用 `--non-interactive`。
- 非 TTY 默认失败并提示显式模式。
- 新增 `.ai/interaction-decisions.yaml`。
- context 和 candidate 决策进入 generated assets、trace 和 review materials。
- 已补充 unit/integration/e2e/acceptance 相关测试。
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_interaction_decisions.py tests/unit/test_write_assets.py tests/integration/test_init_on_fixture_projects.py tests/e2e/test_fixture_end_to_end.py -q
scripts/test-fast.sh
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/harness_builder_agent/tools/generation_trace.py src/harness_builder_agent/tools/interactive_init.py src/harness_builder_agent/tools/asset_writers/human_confirmation.py README.md docs/engineering/init-workflow.md docs/engineering/testing-strategy.md docs/todos/interactive-guided-cli.md tests/integration/test_init_on_fixture_projects.py
git commit -m "docs: mark guided init implemented"
```

---

## Final Verification for This Todo

After all tasks:

Run:

```bash
scripts/test-fast.sh
```

Expected:

- All default tests pass.

Run before push or final goal completion:

```bash
scripts/test-full.sh
```

Expected:

- Fast tests pass.
- Acceptance tests pass against real DeepSeek and real benchmark repositories.

Manual behavior checks:

```bash
.venv/bin/harness-builder-agent init --help
.venv/bin/harness-builder-agent init --non-interactive --repo tests/fixtures/mini-spring-boot
```

Expected:

- Help documents `--non-interactive`.
- Non-interactive init generates `.ai/interaction-decisions.yaml`.

Do not mark `docs/todos/interactive-guided-cli.md` implemented until:

- `.ai/interaction-decisions.yaml` is generated.
- Existing non-interactive automation is explicit and tested.
- Default guided mode is tested with `CliRunner` input.
- Context appears in generated guide content.
- Candidate status decisions are reflected in generated review data.
