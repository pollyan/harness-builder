# Wizard Human Confirmation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add CLI context input and human confirmation assets to `init`.

**Architecture:** Add a small context/questionnaire module, call it from `write_initial_assets`, and expose `--context` as repeatable CLI option. Keep all outputs local under `.ai`.

**Tech Stack:** Python, Typer, YAML, pytest.

---

## File Structure

- Create: `src/harness_builder_agent/tools/human_confirmation.py`
  - Reads context files, builds questionnaire, writes human confirmation markdown.
- Modify: `src/harness_builder_agent/tools/write_assets.py`
  - Accepts context inputs and writes context/questionnaire/human-input assets.
- Modify: `src/harness_builder_agent/cli.py`
  - Adds repeatable `--context` option to `init`.
- Create: `tests/unit/test_human_confirmation.py`
  - Unit tests for context summary and questionnaire builder.
- Modify: `tests/integration/test_init_on_fixture_projects.py`
  - Integration assertions for context and confirmation assets.
- Modify: `src/harness_builder_agent/tools/benchmark.py`
  - Adds confirmation asset checks.
- Modify: `tests/integration/test_benchmark_command.py`
  - Asserts benchmark sees confirmation checks.

## Task 1: Human Confirmation Module

**Files:**
- Create: `tests/unit/test_human_confirmation.py`
- Create: `src/harness_builder_agent/tools/human_confirmation.py`

- [ ] **Step 1: Write failing unit tests**

Test:

```python
from pathlib import Path

from harness_builder_agent.tools.human_confirmation import build_questionnaire, read_context_inputs


def test_read_context_inputs_summarizes_files(tmp_path: Path):
    context = tmp_path / "team-rules.md"
    context.write_text("团队规则" * 700, encoding="utf-8")

    payload = read_context_inputs([context])

    assert payload["schema_version"] == "1.0"
    assert payload["contexts"][0]["path"] == str(context)
    assert payload["contexts"][0]["size_bytes"] > 0
    assert payload["contexts"][0]["truncated"] is True
    assert len(payload["contexts"][0]["summary"]) <= 1200


def test_build_questionnaire_includes_context_guides_sensors_and_warnings():
    questionnaire = build_questionnaire(
        context_inputs={"schema_version": "1.0", "contexts": []},
        scan_metadata={"warnings": [{"code": "command_without_evidence", "message": "Command downgraded"}]},
    )

    ids = {item["interaction_id"] for item in questionnaire["questions"]}
    assert {"confirm:team-context", "confirm:guide-candidates", "confirm:sensor-gates"}.issubset(ids)
    assert "confirm:scan-warning:command_without_evidence" in ids
```

- [ ] **Step 2: Run test to verify failure**

Run: `.venv/bin/python -m pytest tests/unit/test_human_confirmation.py -q`

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement module**

Implement:

- `read_context_inputs(paths: list[Path]) -> dict`
- `build_questionnaire(context_inputs: dict, scan_metadata: dict) -> dict`
- `human_input_markdown(context_inputs: dict, questionnaire: dict) -> str`

- [ ] **Step 4: Run unit tests**

Run: `.venv/bin/python -m pytest tests/unit/test_human_confirmation.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/human_confirmation.py tests/unit/test_human_confirmation.py
git commit -m "feat: add human confirmation assets"
```

## Task 2: Init Integration

**Files:**
- Modify: `src/harness_builder_agent/cli.py`
- Modify: `src/harness_builder_agent/tools/write_assets.py`
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [ ] **Step 1: Write failing integration assertions**

Create a context file in the init test, run:

```python
result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--context", str(context)])
```

Assert:

```python
assert (ai / "context-inputs.yaml").exists()
assert (ai / "questionnaire.yaml").exists()
assert (ai / "human-input-needed.md").exists()
questionnaire = yaml.safe_load((ai / "questionnaire.yaml").read_text())
ids = {item["interaction_id"] for item in questionnaire["questions"]}
assert "confirm:team-context" in ids
assert "confirm:guide-candidates" in ids
assert "confirm:sensor-gates" in ids
assert "团队规则" in (ai / "human-input-needed.md").read_text()
```

- [ ] **Step 2: Run test to verify failure**

Run: `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q`

Expected: FAIL because CLI does not accept `--context` or assets are missing.

- [ ] **Step 3: Implement integration**

- Add `context: list[Path] = typer.Option([], "--context", exists=True, file_okay=True, dir_okay=False)` to `init_command`.
- Pass context paths to `write_initial_assets`.
- Write `context-inputs.yaml`, `questionnaire.yaml`, `human-input-needed.md`.
- Record artifacts in generation trace.

- [ ] **Step 4: Run integration tests**

Run: `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/cli.py src/harness_builder_agent/tools/write_assets.py tests/integration/test_init_on_fixture_projects.py
git commit -m "feat: add init context confirmation outputs"
```

## Task 3: Benchmark Checks and Verification

**Files:**
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/integration/test_benchmark_command.py`

- [ ] **Step 1: Write failing benchmark assertions**

Assert:

```python
assert "schema:questionnaire" in check_ids
assert "content:human-confirmation" in check_ids
```

- [ ] **Step 2: Run benchmark test to verify failure**

Run: `.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q`

Expected: FAIL for missing check ids.

- [ ] **Step 3: Implement benchmark checks**

Add helper that validates:

- `.ai/questionnaire.yaml` has `schema_version=1.0` and non-empty `questions`.
- required ids include `confirm:team-context`, `confirm:guide-candidates`, `confirm:sensor-gates`.
- `.ai/human-input-needed.md` includes `# Human Input Needed`.

- [ ] **Step 4: Run full verification**

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest tests/acceptance/test_real_llm_scan.py -q
.venv/bin/python -m pytest tests/acceptance/test_real_repositories_e2e.py -q
```

Expected: all pass.

- [ ] **Step 5: Commit and push**

```bash
git add src/harness_builder_agent/tools/benchmark.py tests/integration/test_benchmark_command.py
git commit -m "test: benchmark human confirmation assets"
git push origin main
```

