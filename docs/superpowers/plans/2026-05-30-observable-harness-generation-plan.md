# Observable Harness Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local, file-based generation traces for `init`, `assess`, `improve`, and `benchmark`.

**Architecture:** Introduce a focused trace writer that owns `.ai/runs/<run_id>/` artifacts. CLI/tool entry points create a trace, record stage events, register written files, and finalize a machine-readable and human-readable run summary.

**Tech Stack:** Python, Typer CLI, Pydantic-style plain dictionaries, YAML, JSONL, pytest.

---

## File Structure

- Create: `src/harness_builder_agent/tools/generation_trace.py`
  - Owns run id generation, event recording, artifact recording, and final trace files.
- Modify: `src/harness_builder_agent/tools/write_assets.py`
  - Return the generated artifact list and optionally record it into a trace.
- Modify: `src/harness_builder_agent/cli.py`
  - Wrap `init`, `assess`, `improve`, and `benchmark` with trace lifecycle.
- Modify: `src/harness_builder_agent/tools/benchmark.py`
  - Add checks for generation trace existence, schema, and content.
- Create: `tests/unit/test_generation_trace.py`
  - Unit coverage for JSONL/YAML/Markdown trace files.
- Modify: `tests/integration/test_init_on_fixture_projects.py`
  - Assert `init` writes trace files with deep content checks.
- Modify: `tests/integration/test_benchmark_command.py`
  - Assert benchmark validates trace checks.
- Modify: `tests/acceptance/test_real_repositories_e2e.py`
  - Assert real repository runs include trace files and hard gate failure summaries when applicable.

## Task 1: Trace Writer

**Files:**
- Create: `src/harness_builder_agent/tools/generation_trace.py`
- Create: `tests/unit/test_generation_trace.py`

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path

import json
import yaml

from harness_builder_agent.tools.generation_trace import GenerationTrace


def test_generation_trace_writes_events_summary_and_artifacts(tmp_path: Path):
    trace = GenerationTrace.start(tmp_path, command="init", run_id="20260530-120000-init")

    trace.event("scan", "started", "Scan started.")
    trace.event("scan", "completed", "Scan completed.", {"primary_stack": "java-spring", "command_count": 1})
    trace.artifact(tmp_path / ".ai" / "project-inventory.json", "inventory")
    trace.finish("completed", {"primary_stack": "java-spring", "command_count": 1})

    run_dir = tmp_path / ".ai" / "runs" / "20260530-120000-init"
    events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text().splitlines()]
    assert events[0]["stage"] == "scan"
    assert events[0]["event_type"] == "started"
    assert events[1]["details"]["primary_stack"] == "java-spring"

    trace_yaml = yaml.safe_load((run_dir / "trace.yaml").read_text())
    assert trace_yaml["schema_version"] == "1.0"
    assert trace_yaml["status"] == "completed"
    assert trace_yaml["summary"]["primary_stack"] == "java-spring"
    assert trace_yaml["stages"] == ["scan"]

    artifacts = yaml.safe_load((run_dir / "artifacts.yaml").read_text())
    assert artifacts["artifacts"] == [{"path": ".ai/project-inventory.json", "kind": "inventory"}]

    decision_log = (run_dir / "decision-log.md").read_text()
    assert "java-spring" in decision_log
    assert "scan" in decision_log
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_generation_trace.py -q`

Expected: FAIL because `harness_builder_agent.tools.generation_trace` does not exist.

- [ ] **Step 3: Implement trace writer**

Implement `GenerationTrace.start(repo, command, run_id=None)`, `event(stage, event_type, message, details=None)`, `artifact(path, kind)`, and `finish(status, summary=None)`.

Key behavior:

- Create `.ai/runs/<run_id>/`.
- Append events as JSONL.
- Store artifact paths relative to repo with POSIX separators.
- Write `trace.yaml`, `artifacts.yaml`, and `decision-log.md` on `finish`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/test_generation_trace.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/generation_trace.py tests/unit/test_generation_trace.py
git commit -m "feat: add generation trace writer"
```

## Task 2: Init Trace Integration

**Files:**
- Modify: `src/harness_builder_agent/tools/write_assets.py`
- Modify: `src/harness_builder_agent/cli.py`
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [ ] **Step 1: Write failing integration assertions**

In `_assert_init_outputs`, add assertions:

```python
runs = sorted((ai / "runs").iterdir())
assert runs
latest = runs[-1]
trace = yaml.safe_load((latest / "trace.yaml").read_text())
assert trace["command"] == "init"
assert trace["status"] == "completed"
assert {"scan", "weapon-selection", "asset-write"}.issubset(set(trace["stages"]))
assert trace["summary"]["primary_stack"] == expected_stack

artifacts = yaml.safe_load((latest / "artifacts.yaml").read_text())
artifact_paths = {item["path"] for item in artifacts["artifacts"]}
assert ".ai/project-inventory.json" in artifact_paths
assert ".ai/llm-scan-proposal.json" in artifact_paths
assert ".ai/guides/project-context.md" in artifact_paths
assert ".ai/sensors/verification.md" in artifact_paths
assert ".ai/skills/lightweight/SKILL.md" in artifact_paths
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q`

Expected: FAIL because `init` does not write `.ai/runs`.

- [ ] **Step 3: Modify asset writer**

Change `write_initial_assets(repo, inventory, commands, trace=None)` so it:

- Records `weapon-selection.completed` after weapon selection.
- Records every generated file via `trace.artifact(path, kind)`.
- Leaves existing return value as `.ai` path.

- [ ] **Step 4: Modify CLI init**

Wrap `init`:

```python
trace = GenerationTrace.start(repo, "init")
try:
    trace.event("scan", "started", "Repository scan started.")
    inventory, commands = scan_repository(repo)
    trace.event("scan", "completed", "Repository scan completed.", {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)})
    output_dir = write_initial_assets(repo, inventory, commands, trace=trace)
    trace.finish("completed", {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)})
except Exception as exc:
    trace.event("init", "failed", str(exc), {"error_type": type(exc).__name__})
    trace.finish("failed", {"error_type": type(exc).__name__})
    raise
```

- [ ] **Step 5: Run integration test**

Run: `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/harness_builder_agent/cli.py src/harness_builder_agent/tools/write_assets.py tests/integration/test_init_on_fixture_projects.py
git commit -m "feat: trace init generation"
```

## Task 3: Assess, Improve, Benchmark Trace Integration

**Files:**
- Modify: `src/harness_builder_agent/cli.py`
- Modify: `tests/integration/test_assess_improve_commands.py`
- Modify: `tests/integration/test_benchmark_command.py`

- [ ] **Step 1: Write failing tests**

Add assertions that:

- `assess` writes a run with `command=assess` and stage `maturity`.
- `improve` writes a run with `command=improve` and stage `improvement`.
- `benchmark` writes a run with `command=benchmark` and stage `benchmark`.

- [ ] **Step 2: Run tests to verify failure**

Run: `.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py tests/integration/test_benchmark_command.py -q`

Expected: FAIL for missing trace runs.

- [ ] **Step 3: Wrap CLI commands**

Use `GenerationTrace.start(repo, "<command>")` in each command and record:

- `maturity.completed` with paths to `.ai/maturity-report.md` and `.ai/maturity-score.yaml`.
- `improvement.completed` with path to `.ai/improvement-candidates.yaml`.
- `benchmark.completed` or `benchmark.failed` with benchmark status and report path.

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py tests/integration/test_benchmark_command.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/cli.py tests/integration/test_assess_improve_commands.py tests/integration/test_benchmark_command.py
git commit -m "feat: trace harness lifecycle commands"
```

## Task 4: Benchmark Checks for Trace Quality

**Files:**
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/integration/test_benchmark_command.py`

- [ ] **Step 1: Write failing benchmark assertions**

Add expected checks:

```python
assert "exists:runs-trace" in check_ids
assert "schema:generation-trace" in check_ids
assert "content:generation-trace" in check_ids
```

- [ ] **Step 2: Run benchmark test to verify failure**

Run: `.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q`

Expected: FAIL for missing check ids.

- [ ] **Step 3: Implement trace benchmark checks**

Add a `_generation_trace_checks(ai)` helper that:

- Finds latest `.ai/runs/*/trace.yaml`.
- Validates required keys: `schema_version`, `run_id`, `command`, `status`, `stages`, `summary`.
- Requires at least one stage and a matching `events.jsonl`.
- Requires `artifacts.yaml`.

- [ ] **Step 4: Run benchmark tests**

Run: `.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/benchmark.py tests/integration/test_benchmark_command.py
git commit -m "test: benchmark generation trace quality"
```

## Task 5: Acceptance Verification

**Files:**
- Modify: `tests/acceptance/test_real_repositories_e2e.py`

- [ ] **Step 1: Add real repository trace assertions**

Assert:

```python
runs = sorted((ai / "runs").iterdir())
assert runs
trace = yaml.safe_load((runs[-1] / "trace.yaml").read_text())
assert trace["command"] == "benchmark"
assert "benchmark" in trace["stages"]
```

- [ ] **Step 2: Run default tests**

Run: `.venv/bin/python -m pytest -q`

Expected: all tests pass.

- [ ] **Step 3: Run DeepSeek fixture acceptance**

Run: `.venv/bin/python -m pytest tests/acceptance/test_real_llm_scan.py -q`

Expected: PASS.

- [ ] **Step 4: Run real repositories acceptance**

Run: `.venv/bin/python -m pytest tests/acceptance/test_real_repositories_e2e.py -q`

Expected: PASS. RuoYi and eShop may have failed/skipped hard gates, but reports and trace files must make that explicit.

- [ ] **Step 5: Push**

```bash
git push origin main
```

