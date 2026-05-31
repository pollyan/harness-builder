# Self-Improve Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `self-improve` CLI command that generates a review-only maturity-driven self-improvement package.

**Architecture:** Reuse the existing assess, improve, maturity review, and asset candidate tools. Add a small schema and orchestration tool that writes a manifest and Markdown summary without applying formal Harness changes.

**Tech Stack:** Python, Typer, Pydantic, PyYAML, pytest.

---

### Task 1: Manifest Schema

**Files:**
- Create: `src/harness_builder_agent/schemas/self_improve_package.py`
- Modify: `tests/unit/test_schema_contracts.py`

- [ ] **Step 1: Write the failing schema test**

Add a test that validates a `SelfImprovePackageManifest` with `schema_version`, `package_id`, `review_status`, `generated_artifacts`, `candidate_counts`, `maturity`, `next_actions`, and `warnings`.

- [ ] **Step 2: Run the schema test to verify it fails**

Run:

```bash
PATH=/Users/anhui/Documents/myProgram/harness-builder/.venv/bin:$PATH .venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_self_improve_package_manifest_schema -q
```

In this worktree `.venv/bin/python` may not exist. If so, use:

```bash
PATH=/Users/anhui/Documents/myProgram/harness-builder/.venv/bin:$PATH python -m pytest tests/unit/test_schema_contracts.py::test_self_improve_package_manifest_schema -q
```

Expected: import or schema test fails because the schema does not exist.

- [ ] **Step 3: Implement the schema**

Create `SelfImproveGeneratedArtifact`, `SelfImproveCandidateCounts`, `SelfImproveMaturitySnapshot`, and `SelfImprovePackageManifest`. `review_status` must be the literal `pending_harness_maintainer_review`.

- [ ] **Step 4: Run the schema test to verify it passes**

Run the same pytest command. Expected: pass.

### Task 2: Orchestration Tool

**Files:**
- Create: `src/harness_builder_agent/tools/self_improve.py`
- Test: `tests/integration/test_assess_improve_commands.py`

- [ ] **Step 1: Write the failing integration test**

Add `test_self_improve_writes_review_only_package`. It should prepare a fixture repo, monkeypatch LLM maturity review and asset candidate generation, run `self-improve`, validate the manifest and Markdown, assert candidate counts, assert formal guide content is unchanged, assert `.ai/task-runs` is absent, and assert the latest trace command is `self-improve`.

- [ ] **Step 2: Run the integration test to verify it fails**

Run:

```bash
PATH=/Users/anhui/Documents/myProgram/harness-builder/.venv/bin:$PATH python -m pytest tests/integration/test_assess_improve_commands.py::test_self_improve_writes_review_only_package -q
```

Expected: CLI has no `self-improve` command.

- [ ] **Step 3: Implement `run_self_improve`**

The tool should call `assess_maturity`, `generate_improvements`, `review_maturity`, and `generate_asset_candidates`, then read the generated YAML files and write:

- `.ai/review/self-improve-package.yaml`
- `.ai/review/self-improve-package.md`

It should not modify formal Guides, Sensors, Workflow Skills, or `.ai/harness-config.yaml`.

- [ ] **Step 4: Add CLI command**

Add `@app.command("self-improve")` to `cli.py`. The command should create a `GenerationTrace`, record stage events, call `run_self_improve`, record manifest and summary artifacts, and echo the review directory.

- [ ] **Step 5: Run the integration test to verify it passes**

Run the same pytest command. Expected: pass.

### Task 3: Benchmark And Docs

**Files:**
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `docs/engineering/architecture.md`
- Modify: `docs/engineering/testing-strategy.md`
- Modify: `README.md`
- Test: `tests/integration/test_benchmark_command.py`

- [ ] **Step 1: Write the failing benchmark test**

Add assertions that when `self-improve-package.yaml` and `.md` exist, benchmark validates schema, Markdown sections, generated artifact paths, and review-only status.

- [ ] **Step 2: Run the benchmark test to verify it fails**

Run:

```bash
PATH=/Users/anhui/Documents/myProgram/harness-builder/.venv/bin:$PATH python -m pytest tests/integration/test_benchmark_command.py::test_benchmark_validates_self_improve_package_artifact -q
```

Expected: benchmark lacks the new optional artifact check.

- [ ] **Step 3: Implement benchmark validation**

Add optional validation for `.ai/review/self-improve-package.yaml` and `.md`. It should fail if schema is invalid, Markdown is missing required sections, generated artifact paths do not start with `.ai/`, or review status is not pending.

- [ ] **Step 4: Update docs**

Document `self-improve` as a review-only orchestration command. State that it does not execute Runtime workflows and does not create `.ai/task-runs`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
PATH=/Users/anhui/Documents/myProgram/harness-builder/.venv/bin:$PATH python -m pytest tests/unit/test_schema_contracts.py::test_self_improve_package_manifest_schema tests/integration/test_assess_improve_commands.py::test_self_improve_writes_review_only_package tests/integration/test_benchmark_command.py::test_benchmark_validates_self_improve_package_artifact -q
```

Expected: all pass.

### Task 4: Verification And Self-Harness Gate

**Files:**
- Review: `docs/todos/README.md`
- Review: `docs/engineering/`

- [ ] **Step 1: Run run-boundary checks**

Run:

```bash
rg -n '@app\.command\("run|run_task|run_sensor|harness-builder-agent run' src tests README.md docs/engineering
find tests/fixtures -path '*task-runs*' -maxdepth 8 -print
```

Expected: no Builder `run` command and no fixture task-runs.

- [ ] **Step 2: Run fast regression before commit**

Run:

```bash
PATH=/Users/anhui/Documents/myProgram/harness-builder/.venv/bin:$PATH scripts/test-fast.sh
```

Expected: all fast tests pass.

- [ ] **Step 3: Self-Harness Improvement Gate**

Record in the final response whether docs, todos, fixture/e2e/acceptance, benchmark, or schema tests need a follow-up. If a follow-up is larger than this milestone, add a todo.

- [ ] **Step 4: Commit**

Run:

```bash
git add README.md docs/engineering docs/superpowers src tests
git commit -m "feat: add self-improve package command"
```
