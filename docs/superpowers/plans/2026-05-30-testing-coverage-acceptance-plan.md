# Testing Coverage and Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen Harness Builder's regression, boundary, and acceptance coverage before larger refactors and interactive CLI work.

**Architecture:** Add focused tests around existing modules first, then make the smallest production changes required by the tests. Keep default regression fast, add explicit acceptance scripts, and preserve current business behavior except for the confirmed CLI improvement that `init` defaults to the current working directory.

**Tech Stack:** Python 3.11+, pytest, Typer CliRunner, Pydantic, YAML, Bash scripts.

---

## File Structure

Create or modify:

- Modify: `src/harness_builder_agent/cli.py`
  - Make `init --repo` optional and default to `Path.cwd()`.
- Modify: `tests/unit/test_cli_import.py`
  - Fix command visibility test to cover all five commands.
- Modify: `tests/integration/test_init_on_fixture_projects.py`
  - Add test for `init` defaulting to current working directory.
- Modify: `tests/unit/test_schema_contracts.py`
  - Add positive and negative schema tests for key machine-consumed schemas.
- Create: `tests/unit/test_weapon_library.py`
  - Directly test built-in weapon library selection.
- Create: `tests/unit/test_write_assets.py`
  - Establish behavior baseline for `write_initial_assets`.
- Modify: `tests/integration/test_benchmark_command.py`
  - Add benchmark failure-path tests.
- Modify: `tests/integration/test_task_run_workflow.py`
  - Add run task boundary tests.
- Modify: `tests/integration/test_assess_improve_commands.py`
  - Add assess/improve boundary tests.
- Create: `scripts/test-fast.sh`
  - Run default regression.
- Create: `scripts/test-acceptance.sh`
  - Run acceptance tests explicitly.
- Create: `scripts/test-full.sh`
  - Run fast then acceptance.
- Modify: `.githooks/pre-commit`
  - Call `scripts/test-fast.sh`.
- Modify: `.githooks/pre-push`
  - Call `scripts/test-fast.sh`.
- Modify: `scripts/install-git-hooks.sh`
  - Mark new scripts executable.
- Modify: `README.md`
  - Document fast, full, and acceptance test commands.
- Modify: `docs/engineering/testing-strategy.md`
  - Align testing strategy with scripts and hooks.

---

### Task 1: CLI Contract and `init` Current Directory Default

**Files:**
- Modify: `tests/unit/test_cli_import.py`
- Modify: `tests/integration/test_init_on_fixture_projects.py`
- Modify: `src/harness_builder_agent/cli.py`

- [ ] **Step 1: Update CLI command visibility test**

Replace the test in `tests/unit/test_cli_import.py` with:

```python
from typer.testing import CliRunner

from harness_builder_agent.cli import app


def test_cli_exposes_required_commands():
    runner = CliRunner()

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in ("init", "run", "benchmark", "assess", "improve"):
        assert command in result.output
```

- [ ] **Step 2: Add failing integration test for cwd default**

Append to `tests/integration/test_init_on_fixture_projects.py`:

```python
def test_init_defaults_to_current_working_directory(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(app, ["init"], env={}, catch_exceptions=False, color=False, prog_name="harness-builder-agent", obj=None)

    assert result.exit_code != 0
```

Then replace that temporary assertion with the real cwd invocation:

```python
def test_init_defaults_to_current_working_directory(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(app, ["init"], cwd=repo)

    assert result.exit_code == 0, result.output
    _assert_init_outputs(repo, "java-spring")
```

The first version verifies the current required `--repo` behavior fails. The final version defines the desired behavior.

- [ ] **Step 3: Run the focused tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_cli_import.py tests/integration/test_init_on_fixture_projects.py::test_init_defaults_to_current_working_directory -q
```

Expected before implementation: CLI import test passes, cwd default integration test fails because `--repo` is required.

- [ ] **Step 4: Implement `Path.cwd()` default**

Change `init_command` in `src/harness_builder_agent/cli.py`:

```python
@app.command("init")
def init_command(
    repo: Optional[Path] = typer.Option(None, "--repo", file_okay=False, dir_okay=True),
    context: Optional[list[Path]] = typer.Option(None, "--context", exists=True, file_okay=True, dir_okay=False),
) -> None:
    """Scan a repository and generate initial .ai harness assets."""
    target_repo = (repo or Path.cwd()).resolve()
    if not target_repo.exists() or not target_repo.is_dir():
        raise typer.BadParameter(f"Repository path must be an existing directory: {target_repo}")
    trace = GenerationTrace.start(target_repo, "init")
    try:
        trace.event("scan", "started", "Repository scan started.")
        inventory, commands = scan_repository(target_repo)
        trace.event(
            "scan",
            "completed",
            "Repository scan completed.",
            {"primary_stack": inventory.primary_stack, "stacks": inventory.stacks, "command_count": len(commands.commands)},
        )
        output_dir = write_initial_assets(target_repo, inventory, commands, trace=trace, context_paths=context or [])
        trace.finish("completed", {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)})
    except Exception as exc:
        trace.event("init", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    typer.echo(f"Generated harness assets in {output_dir}")
```

- [ ] **Step 5: Run focused tests and full default regression**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_cli_import.py tests/integration/test_init_on_fixture_projects.py -q
.venv/bin/python -m pytest -q
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/harness_builder_agent/cli.py tests/unit/test_cli_import.py tests/integration/test_init_on_fixture_projects.py
git commit -m "test: cover cli init defaults"
```

---

### Task 2: Schema Contract Positive and Negative Tests

**Files:**
- Modify: `tests/unit/test_schema_contracts.py`

- [ ] **Step 1: Add schema imports and validation helpers**

Add imports:

```python
import pytest
from pydantic import ValidationError

from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.harness_map import HarnessMap
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.sensor_report import SensorReport
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
```

- [ ] **Step 2: Add failing schema tests**

Append tests:

```python
def test_harness_map_requires_existing_contract_fields():
    payload = {
        "task_id": "demo-task-001",
        "task_type": "bugfix",
        "selected_workflow": "bugfix",
        "risk_level": "low",
        "guide_policy": {"required": [".ai/guides/project-context.md"]},
        "sensor_policy": {"hard_gates": ["unit_test"]},
        "workflow_skill": {"path": ".ai/skills/bugfix/SKILL.md"},
    }

    model = HarnessMap.model_validate(payload)

    assert model.selected_workflow == "bugfix"
    assert model.workflow_skill["path"].endswith("SKILL.md")


def test_sensor_report_rejects_unknown_status():
    payload = {
        "task_id": "demo-task-001",
        "sensor_results": [{"id": "unit_test", "command": "pytest", "status": "maybe", "summary": "unknown"}],
    }

    with pytest.raises(ValidationError):
        SensorReport.model_validate(payload)


def test_benchmark_report_requires_check_statuses():
    payload = {"schema_version": "1.0", "repo_name": "demo", "profile": "java-spring", "status": "passed", "checks": []}

    report = BenchmarkReport.model_validate(payload)

    assert report.status == "passed"


def test_weapon_library_selection_requires_candidate_lists():
    payload = {
        "schema_version": "1.0",
        "source": "built_in_weapon_library",
        "primary_stack": "java-spring",
        "selected_stacks": ["common", "java-spring"],
        "guide_weapon_ids": ["common.guide.project-context"],
        "sensor_weapon_ids": ["common.sensor.test-command"],
        "guide_weapons": [],
        "sensor_weapons": [],
    }

    selection = WeaponLibrarySelection.model_validate(payload)

    assert selection.source == "built_in_weapon_library"


def test_maturity_report_requires_dimension_scores():
    payload = {
        "schema_version": "1.0",
        "overall_level": "L2",
        "dimension_scores": {"guides": "L1"},
        "evidence": ["generated guides"],
        "blocking_reasons": ["needs review"],
        "recommended_next_steps": ["confirm rules"],
    }

    report = MaturityReport.model_validate(payload)

    assert report.dimension_scores["guides"] == "L1"


def test_improvement_candidates_require_human_confirmation_flag():
    payload = {
        "schema_version": "1.0",
        "candidates": [
            {
                "id": "candidate-1",
                "candidate_type": "guide_update",
                "summary": "Add testing guide",
                "suggested_target": ".ai/guides/testing.md",
                "human_confirmation_required": True,
            }
        ],
    }

    report = ImprovementCandidateReport.model_validate(payload)

    assert report.candidates[0].human_confirmation_required is True
```

- [ ] **Step 3: Run schema tests and fix payloads if model names differ**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py -q
```

Expected: tests pass if payloads match current schema. If a payload does not match the actual schema, inspect the schema file and update the test to assert the real contract, not a guessed one.

- [ ] **Step 4: Commit**

```bash
git add tests/unit/test_schema_contracts.py
git commit -m "test: expand schema contract coverage"
```

---

### Task 3: Weapon Library Unit Tests

**Files:**
- Create: `tests/unit/test_weapon_library.py`

- [ ] **Step 1: Write tests**

Create:

```python
from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.weapon_library import select_weapon_library


def _inventory(primary_stack: str) -> ProjectInventory:
    return ProjectInventory(repo_name="demo", root_path="/tmp/demo", primary_stack=primary_stack, stacks=[primary_stack])


def _commands() -> CommandCatalog:
    return CommandCatalog(commands=[CommandDefinition(id="unit_test", command="pytest", type="test", gate="hard", source="pyproject.toml")])


def test_selects_common_and_java_spring_weapons():
    selection = select_weapon_library(_inventory("java-spring"), _commands())

    assert selection.source == "built_in_weapon_library"
    assert {"common", "java-spring"}.issubset(set(selection.selected_stacks))
    assert any(item.startswith("java-spring.guide.") for item in selection.guide_weapon_ids)
    assert any(item.startswith("java-spring.sensor.") for item in selection.sensor_weapon_ids)


def test_selects_common_and_dotnet_weapons():
    selection = select_weapon_library(_inventory("dotnet-aspnet"), _commands())

    assert {"common", "dotnet-aspnet"}.issubset(set(selection.selected_stacks))
    assert any(item.startswith("dotnet-aspnet.guide.") for item in selection.guide_weapon_ids)
    assert any(item.startswith("dotnet-aspnet.sensor.") for item in selection.sensor_weapon_ids)


def test_unknown_stack_keeps_common_floor():
    selection = select_weapon_library(_inventory("unknown"), _commands())

    assert "common" in selection.selected_stacks
    assert selection.primary_stack == "unknown"
    assert all(item.startswith("common.") for item in selection.guide_weapon_ids + selection.sensor_weapon_ids)
```

- [ ] **Step 2: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_weapon_library.py -q
```

Expected: pass. If unknown stack currently includes other stacks, update implementation or test to preserve the intended common-only floor.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_weapon_library.py
git commit -m "test: cover weapon library selection"
```

---

### Task 4: Write Assets Behavior Baseline

**Files:**
- Create: `tests/unit/test_write_assets.py`

- [ ] **Step 1: Write baseline tests**

Create:

```python
from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.write_assets import write_initial_assets


def _inventory(tmp_path: Path) -> ProjectInventory:
    return ProjectInventory(
        repo_name="demo",
        root_path=str(tmp_path),
        primary_stack="java-spring",
        stacks=["java", "maven", "spring-boot"],
        modules=[{"name": "app", "path": ".", "kind": "backend"}],
        evidence=[{"path": "pom.xml", "reason": "maven build file"}],
        stack_extensions={
            "scan_metadata": {
                "schema_version": "1.0",
                "llm_status": "succeeded",
                "prompt_version": "test",
                "evidence_file_count": 1,
                "warnings": [],
            },
            "llm_scan_proposal": {
                "schema_version": "1.0",
                "primary_stack": "java-spring",
                "stacks": ["java", "maven"],
                "modules": [{"name": "app", "path": ".", "kind": "backend"}],
                "architecture_signals": ["Controller layer"],
                "risk_areas": [{"path": "src/main/resources/application.yml", "reason": "database config"}],
                "command_candidates": [
                    {"id": "unit_test", "command": "mvn test", "type": "test", "gate": "hard", "source": "pom.xml", "confidence": "high"}
                ],
                "configs": [],
                "ci_files": [],
                "confidence": "high",
                "needs_human_confirmation": False,
                "reasoning_summary": "test proposal",
            },
        },
    )


def _commands() -> CommandCatalog:
    return CommandCatalog(commands=[CommandDefinition(id="unit_test", command="mvn test", type="test", gate="hard", source="pom.xml")])


def test_write_initial_assets_generates_core_guides_sensors_skills_and_trace(tmp_path: Path):
    context = tmp_path / "team-rules.md"
    context.write_text("团队规则：Controller 只能调用 Service。", encoding="utf-8")
    trace = GenerationTrace.start(tmp_path, "init", run_id="20260530-120000-init")

    ai = write_initial_assets(tmp_path, _inventory(tmp_path), _commands(), trace=trace, context_paths=[context])
    trace.finish("completed", {"primary_stack": "java-spring"})

    assert (ai / "project-inventory.json").exists()
    assert (ai / "command-catalog.yaml").exists()
    assert (ai / "harness-config.yaml").exists()
    assert (ai / "guides" / "project-context.md").exists()
    assert (ai / "sensors" / "verification.md").exists()
    assert (ai / "skills" / "lightweight" / "SKILL.md").exists()
    assert (ai / "skills" / "bugfix" / "SKILL.md").exists()

    guide = (ai / "guides" / "project-context.md").read_text(encoding="utf-8")
    assert "## 当前项目事实" in guide
    assert "java-spring.guide." in guide

    sensor = (ai / "sensors" / "verification.md").read_text(encoding="utf-8")
    assert "## 已发现的验证命令" in sensor
    assert "common.sensor." in sensor

    human_input = (ai / "human-input-needed.md").read_text(encoding="utf-8")
    assert "团队规则" in human_input

    candidates = yaml.safe_load((ai / "experience" / "weapon-library-candidates.yaml").read_text(encoding="utf-8"))
    assert candidates["candidates"]
    assert all(item["human_confirmation_required"] is True for item in candidates["candidates"])

    artifacts = yaml.safe_load((ai / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text(encoding="utf-8"))
    artifact_paths = {item["path"] for item in artifacts["artifacts"]}
    assert ".ai/project-inventory.json" in artifact_paths
    assert ".ai/guides/project-context.md" in artifact_paths
    assert ".ai/sensors/verification.md" in artifact_paths
```

- [ ] **Step 2: Run test**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_write_assets.py -q
```

Expected: pass.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_write_assets.py
git commit -m "test: baseline initial asset writing"
```

---

### Task 5: Benchmark Failure Path Tests

**Files:**
- Modify: `tests/integration/test_benchmark_command.py`

- [ ] **Step 1: Add helper to prepare benchmark repo**

Add a helper that generates a benchmarkable repo with passed sensors:

```python
def _prepare_benchmark_repo(tmp_path: Path, monkeypatch, fixture_name: str = "mini-spring-boot", profile: str = "java-spring") -> Path:
    repo = tmp_path / fixture_name
    shutil.copytree(FIXTURES / fixture_name, repo)
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", lambda repo_path: _fake_scan(repo_path, profile))
    monkeypatch.setattr("harness_builder_agent.tools.run_task.run_sensor", _passed_sensor)
    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", profile])
    assert result.exit_code == 0, result.output
    return repo
```

- [ ] **Step 2: Add failing-path tests**

Append:

```python
def test_benchmark_fails_when_required_file_is_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_benchmark_repo(tmp_path, monkeypatch)
    (repo / ".ai" / "project-inventory.json").unlink()

    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "java-spring"])

    assert result.exit_code == 1, result.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text())
    assert report["status"] == "failed"
    assert any(check["id"] == "exists:project-inventory.json" and check["passed"] is False for check in report["checks"])


def test_benchmark_fails_when_guide_required_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_benchmark_repo(tmp_path, monkeypatch)
    (repo / ".ai" / "guides" / "project-context.md").write_text("# Project Context\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "java-spring"])

    assert result.exit_code == 1, result.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text())
    guide_check = next(check for check in report["checks"] if check["id"] == "content:guides-quality")
    assert guide_check["passed"] is False


def test_benchmark_fails_when_workflow_skill_reference_is_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_benchmark_repo(tmp_path, monkeypatch)
    (repo / ".ai" / "skills" / "bugfix" / "SKILL.md").unlink()

    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "java-spring"])

    assert result.exit_code == 1, result.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text())
    skill_check = next(check for check in report["checks"] if check["id"] == "content:workflow-skills")
    assert skill_check["passed"] is False
```

- [ ] **Step 3: Run benchmark tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q
```

Expected: new tests expose any benchmark regeneration behavior that masks broken files. If benchmark always regenerates assets before checking, update the tests to call the internal check helpers directly or adjust benchmark design in the next plan revision.

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_benchmark_command.py
git commit -m "test: cover benchmark failure paths"
```

---

### Task 6: Run Task Boundary Tests

**Files:**
- Modify: `tests/integration/test_task_run_workflow.py`

- [ ] **Step 1: Add failed and skipped sensor helpers**

Add:

```python
def _failed_sensor(_repo, command):
    return {
        "id": command.id,
        "command": command.command,
        "status": "failed",
        "exit_code": 1,
        "duration_seconds": 0.01,
        "summary": "Sensor failed.",
    }


def _skipped_sensor(_repo, command):
    return {
        "id": command.id,
        "command": command.command,
        "status": "skipped",
        "exit_code": None,
        "duration_seconds": 0.0,
        "summary": "Executable missing.",
    }
```

- [ ] **Step 2: Add boundary tests**

Append:

```python
def test_run_records_failed_sensor_status(tmp_path: Path, monkeypatch):
    repo = _prepared_repo(tmp_path, "mini-spring-boot", "java-spring", monkeypatch)
    monkeypatch.setattr("harness_builder_agent.tools.run_task.run_sensor", _failed_sensor)

    result = CliRunner().invoke(app, ["run", "--repo", str(repo), "修复登录接口错误提示不一致的问题"])

    assert result.exit_code == 0, result.output
    report = yaml.safe_load((repo / ".ai" / "task-runs" / "demo-task-001" / "sensor-report.yaml").read_text())
    assert report["sensor_results"][0]["status"] == "failed"
    runtime = yaml.safe_load((repo / ".ai" / "task-runs" / "demo-task-001" / "runtime-summary.yaml").read_text())
    assert "failed" in runtime["sensor_statuses"]


def test_run_marks_missing_guide_in_used_guides(tmp_path: Path, monkeypatch):
    repo = _prepared_repo(tmp_path, "mini-spring-boot", "java-spring", monkeypatch)
    (repo / ".ai" / "guides" / "architecture.md").unlink()

    result = CliRunner().invoke(app, ["run", "--repo", str(repo), "修复登录接口错误提示不一致的问题"])

    assert result.exit_code == 0, result.output
    used_guides = yaml.safe_load((repo / ".ai" / "task-runs" / "demo-task-001" / "used-guides.yaml").read_text())
    assert any(item["exists"] is False for item in used_guides["required_guides"])
```

- [ ] **Step 3: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_task_run_workflow.py -q
```

Expected: tests pass or reveal current behavior that needs minimal adjustment.

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_task_run_workflow.py
git commit -m "test: cover runtime workflow boundaries"
```

---

### Task 7: Assess and Improve Boundary Tests

**Files:**
- Modify: `tests/integration/test_assess_improve_commands.py`

- [ ] **Step 1: Add command-catalog-empty maturity test**

Append:

```python
def test_assess_handles_empty_command_catalog(tmp_path: Path, monkeypatch):
    repo = _prepared_task_repo(tmp_path, "mini-spring-boot", "java-spring", monkeypatch)
    (repo / ".ai" / "command-catalog.yaml").write_text("schema_version: '1.0'\ncommands: []\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["assess", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    score = yaml.safe_load((repo / ".ai" / "maturity-score.yaml").read_text(encoding="utf-8"))
    assert score["schema_version"] == "1.0"
    assert score["dimension_scores"]["sensors"] in {"L0", "L1"}
```

- [ ] **Step 2: Add improve candidate target test**

Append:

```python
def test_improve_candidates_are_reviewable_and_target_ai_assets(tmp_path: Path, monkeypatch):
    repo = _prepared_task_repo(tmp_path, "mini-dotnet-webapi", "dotnet-aspnet", monkeypatch)

    result = CliRunner().invoke(app, ["improve", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    candidates = yaml.safe_load((repo / ".ai" / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    assert candidates["candidates"]
    assert all(item["human_confirmation_required"] is True for item in candidates["candidates"])
    assert all(item["suggested_target"].startswith(".ai/") for item in candidates["candidates"])
```

- [ ] **Step 3: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py -q
```

Expected: pass or expose maturity behavior to adjust minimally.

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_assess_improve_commands.py
git commit -m "test: cover maturity and improvement boundaries"
```

---

### Task 8: Acceptance Scripts and Documentation

**Files:**
- Create: `scripts/test-fast.sh`
- Create: `scripts/test-acceptance.sh`
- Create: `scripts/test-full.sh`
- Modify: `.githooks/pre-commit`
- Modify: `.githooks/pre-push`
- Modify: `scripts/install-git-hooks.sh`
- Modify: `README.md`
- Modify: `docs/engineering/testing-strategy.md`

- [ ] **Step 1: Create test scripts**

Create `scripts/test-fast.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="python"
  echo "Using fallback python from PATH because .venv/bin/python is not available."
fi

"$PYTHON" -m pytest -q
```

Create `scripts/test-acceptance.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="python"
  echo "Using fallback python from PATH because .venv/bin/python is not available."
fi

"$PYTHON" -m pytest tests/acceptance -q
```

Create `scripts/test-full.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

scripts/test-fast.sh
scripts/test-acceptance.sh
```

- [ ] **Step 2: Update hooks**

Change `.githooks/pre-commit` to call:

```bash
scripts/test-fast.sh
```

Change `.githooks/pre-push` to call:

```bash
scripts/test-fast.sh
```

- [ ] **Step 3: Update installer**

In `scripts/install-git-hooks.sh`, ensure:

```bash
chmod +x .githooks/pre-commit .githooks/post-commit .githooks/pre-push scripts/check-ci.sh scripts/test-fast.sh scripts/test-acceptance.sh scripts/test-full.sh
```

- [ ] **Step 4: Update docs**

In `README.md` testing section, document:

```bash
scripts/test-fast.sh
scripts/test-acceptance.sh
scripts/test-full.sh
```

In `docs/engineering/testing-strategy.md`, align the strategy with fast, acceptance, and full tiers.

- [ ] **Step 5: Run scripts**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

Run only if DeepSeek key and benchmark repos are available:

```bash
scripts/test-acceptance.sh
```

Expected: pass when environment is configured; otherwise fail loudly with missing key, missing repo, network, or API error.

- [ ] **Step 6: Commit**

```bash
git add scripts/test-fast.sh scripts/test-acceptance.sh scripts/test-full.sh .githooks/pre-commit .githooks/pre-push scripts/install-git-hooks.sh README.md docs/engineering/testing-strategy.md
git commit -m "test: add local verification scripts"
```

---

### Task 9: Final Regression and Todo Status Update

**Files:**
- Modify: `docs/todos/testing-coverage-and-acceptance-strategy.md`

- [ ] **Step 1: Run default regression**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected: pass.

- [ ] **Step 2: Run fast script**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [ ] **Step 3: Attempt acceptance script**

Run:

```bash
scripts/test-acceptance.sh
```

Expected: pass if environment is fully configured. If it fails due to missing key, missing `.benchmarks`, network, or API error, record the exact reason in the final response and do not claim acceptance passed.

- [ ] **Step 4: Update todo status**

If implementation and verification are complete, update `docs/todos/testing-coverage-and-acceptance-strategy.md`:

```markdown
- 状态：implemented
```

Add an implementation note:

```markdown
## 实现结果

- 已补充 CLI、schema、weapon library、asset writer、benchmark、run task、assess/improve 的关键测试。
- 已新增 fast、acceptance、full 三层本地验证脚本。
- Acceptance 仍然显式运行，不进入默认 CI。
```

- [ ] **Step 5: Commit**

```bash
git add docs/todos/testing-coverage-and-acceptance-strategy.md
git commit -m "docs: mark testing coverage todo implemented"
```

